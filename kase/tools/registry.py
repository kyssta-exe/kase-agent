"""Central tool registry for the Kase Agent."""

import asyncio
import concurrent.futures
import importlib
import json
import logging
import threading
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_CHECK_FN_TTL_SECONDS = 30.0
_check_fn_cache: Dict[Callable, tuple[float, bool]] = {}
_check_fn_cache_lock = threading.Lock()
_discovery_cache = {"result": None, "ts": 0.0}
_DISCOVERY_TTL = 5.0
_UNKNOWN_TOOL_JSON = json.dumps({"error": "Unknown tool: %s"})
_ERROR_JSON = json.dumps({"error": "%s"})


def _check_fn_cached(fn: Callable) -> bool:
    now = time.monotonic()
    with _check_fn_cache_lock:
        cached = _check_fn_cache.get(fn)
        if cached is not None:
            ts, value = cached
            if now - ts < _CHECK_FN_TTL_SECONDS:
                return value
    try:
        value = bool(fn())
    except Exception:
        value = False
    with _check_fn_cache_lock:
        _check_fn_cache[fn] = (now, value)
    return value


def invalidate_check_fn_cache() -> None:
    with _check_fn_cache_lock:
        _check_fn_cache.clear()


_TOOL_REGISTER_SIGNATURE = "registry.register("


@lru_cache(maxsize=1)
def _cached_tool_files(tools_path: Path) -> List[str]:
    return sorted(
        p.stem for p in tools_path.glob("*.py")
        if p.name not in {"__init__.py", "registry.py"}
        and _TOOL_REGISTER_SIGNATURE in p.read_text(encoding="utf-8")
    )


def discover_builtin_tools(tools_dir: Optional[Path] = None) -> List[str]:
    tools_path = tools_dir or Path(__file__).resolve().parent
    imported: List[str] = []
    for stem in _cached_tool_files(tools_path):
        mod_name = f"kase.tools.{stem}"
        try:
            importlib.import_module(mod_name)
            imported.append(mod_name)
        except Exception as e:
            logger.warning("Could not import tool module %s: %s", mod_name, e)
    return imported


class ToolEntry:
    __slots__ = (
        "name", "toolset", "schema", "handler", "check_fn",
        "requires_env", "is_async", "description", "emoji",
        "max_result_size_chars", "dynamic_schema_overrides",
    )

    def __init__(self, name, toolset, schema, handler, check_fn=None,
                 requires_env=None, is_async=False, description="", emoji="",
                 max_result_size_chars=None, dynamic_schema_overrides=None):
        self.name = name
        self.toolset = toolset
        self.schema = schema
        self.handler = handler
        self.check_fn = check_fn
        self.requires_env = requires_env or []
        self.is_async = is_async
        self.description = description or schema.get("description", "")
        self.emoji = emoji
        self.max_result_size_chars = max_result_size_chars
        self.dynamic_schema_overrides = dynamic_schema_overrides


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}
        self._toolset_checks: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._generation: int = 0

    def register(
        self, name: str, toolset: str, schema: dict, handler: Callable,
        check_fn: Callable = None, requires_env: list = None,
        is_async: bool = False, description: str = "", emoji: str = "",
        max_result_size_chars: Optional[int] = None,
        dynamic_schema_overrides: Callable = None, override: bool = False,
    ):
        with self._lock:
            existing = self._tools.get(name)
            if existing and existing.toolset != toolset and not override:
                logger.error("Tool '%s' rejected: would shadow '%s'", name, existing.toolset)
                return
            if existing and existing.toolset == toolset:
                logger.debug("Tool '%s' re-registered in same toolset", name)
            
            self._tools[name] = ToolEntry(
                name=name, toolset=toolset, schema=schema, handler=handler,
                check_fn=check_fn, requires_env=requires_env, is_async=is_async,
                description=description, emoji=emoji,
                max_result_size_chars=max_result_size_chars,
                dynamic_schema_overrides=dynamic_schema_overrides,
            )
            if check_fn and toolset not in self._toolset_checks:
                self._toolset_checks[toolset] = check_fn
            self._generation += 1

    def deregister(self, name: str) -> None:
        with self._lock:
            entry = self._tools.pop(name, None)
            if entry is None:
                return
            toolset_still_exists = any(e.toolset == entry.toolset for e in self._tools.values())
            if not toolset_still_exists:
                self._toolset_checks.pop(entry.toolset, None)
            self._generation += 1

    def get_entry(self, name: str) -> Optional[ToolEntry]:
        with self._lock:
            return self._tools.get(name)

    def get_definitions(self, tool_names: Set[str], quiet: bool = False) -> List[dict]:
        result = []
        check_results: Dict[Callable, bool] = {}
        with self._lock:
            entries = dict(self._tools)
        for name in sorted(tool_names):
            entry = entries.get(name)
            if not entry:
                continue
            if entry.check_fn:
                if entry.check_fn not in check_results:
                    check_results[entry.check_fn] = _check_fn_cached(entry.check_fn)
                if not check_results[entry.check_fn]:
                    continue
            schema_with_name = {**entry.schema, "name": entry.name}
            if entry.dynamic_schema_overrides is not None:
                try:
                    overrides = entry.dynamic_schema_overrides()
                    if isinstance(overrides, dict):
                        schema_with_name.update(overrides)
                except Exception as exc:
                    logger.warning("dynamic_schema_overrides for %s failed: %s", name, exc)
            result.append({"type": "function", "function": schema_with_name})
        return result

    def dispatch(self, name: str, args: dict, **kwargs) -> str:
        entry = self.get_entry(name)
        if not entry:
            return _UNKNOWN_TOOL_JSON % name
        try:
            if entry.is_async:
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            return pool.submit(entry.handler, args, **kwargs).result()
                except RuntimeError:
                    pass
                return asyncio.run(entry.handler(args, **kwargs))
            return entry.handler(args, **kwargs)
        except Exception as e:
            logger.exception("Tool %s error: %s", name, e)
            return _ERROR_JSON % f"{type(e).__name__}: {e}"

    def get_all_tool_names(self) -> List[str]:
        with self._lock:
            return sorted(self._tools.keys())

    def get_schema(self, name: str) -> Optional[dict]:
        entry = self.get_entry(name)
        return entry.schema if entry else None

    def get_toolset_for_tool(self, name: str) -> Optional[str]:
        entry = self.get_entry(name)
        return entry.toolset if entry else None

    def get_emoji(self, name: str, default: str = "⚡") -> str:
        entry = self.get_entry(name)
        return (entry.emoji if entry and entry.emoji else default)

    def is_toolset_available(self, toolset: str) -> bool:
        with self._lock:
            check = self._toolset_checks.get(toolset)
        if not check:
            return True
        try:
            return bool(check())
        except Exception:
            return False

    def check_tool_availability(self) -> tuple[list, list]:
        available = []
        unavailable = []
        seen = set()
        with self._lock:
            entries = list(self._tools.values())
            checks = dict(self._toolset_checks)
        for entry in entries:
            ts = entry.toolset
            if ts in seen:
                continue
            seen.add(ts)
            check = checks.get(ts)
            if check is None:
                available.append(ts)
            else:
                try:
                    if bool(check()):
                        available.append(ts)
                    else:
                        unavailable.append({"name": ts, "env_vars": entry.requires_env})
                except Exception:
                    unavailable.append({"name": ts, "env_vars": entry.requires_env})
        return available, unavailable


registry = ToolRegistry()


def tool_error(message, **extra) -> str:
    result = {"error": str(message)}
    if extra:
        result.update(extra)
    return json.dumps(result, ensure_ascii=False)


def tool_result(data=None, **kwargs) -> str:
    if data is not None:
        return json.dumps(data, ensure_ascii=False)
    return json.dumps(kwargs, ensure_ascii=False)
