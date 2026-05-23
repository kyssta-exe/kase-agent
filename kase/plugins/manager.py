"""Plugin discovery and management."""

import importlib
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginContext:
    def __init__(self):
        self._tools: List[dict] = []
        self._hooks: Dict[str, List[Callable]] = {}
        self._cli_commands: List[dict] = []

    def register_tool(self, name: str, schema: dict, handler: Callable, toolset: str = "plugin"):
        from kase.tools.registry import registry
        registry.register(name=name, toolset=toolset, schema=schema, handler=handler)
        self._tools.append({"name": name, "toolset": toolset})

    def register_hook(self, event: str, handler: Callable):
        self._hooks.setdefault(event, []).append(handler)

    def register_cli_command(self, name: str, handler: Callable, help_text: str = ""):
        self._cli_commands.append({"name": name, "handler": handler, "help": help_text})

    def get_hooks(self, event: str) -> List[Callable]:
        return self._hooks.get(event, [])


class PluginManager:
    def __init__(self):
        self._plugins: Dict[str, PluginContext] = {}
        self._discovered = False

    def discover_plugins(self, plugin_dirs: Optional[List[Path]] = None) -> None:
        if self._discovered:
            return
        self._discovered = True
        
        dirs = plugin_dirs or [
            Path(__file__).resolve().parent.parent / "plugins",
            Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "plugins",
        ]
        
        for plugin_dir in dirs:
            if not plugin_dir.exists():
                continue
            for item in plugin_dir.iterdir():
                if item.is_dir() and (item / "__init__.py").exists():
                    self._load_plugin(item)

    def _load_plugin(self, plugin_dir: Path) -> None:
        name = plugin_dir.name
        try:
            ctx = PluginContext()
            try:
                mod = importlib.import_module(f"kase.plugins.{name}")
            except ModuleNotFoundError:
                mod = importlib.import_module(f"plugins.{name}")
            if hasattr(mod, "register"):
                mod.register(ctx)
                self._plugins[name] = ctx
                logger.info("Loaded plugin: %s", name)
        except Exception as e:
            logger.warning("Failed to load plugin %s: %s", name, e)

    def get_plugin(self, name: str) -> Optional[PluginContext]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())

    def run_hooks(self, event: str, *args, **kwargs) -> None:
        for ctx in self._plugins.values():
            for hook in ctx.get_hooks(event):
                try:
                    hook(*args, **kwargs)
                except Exception as e:
                    logger.warning("Hook %s failed in plugin: %s", event, e)


plugin_manager = PluginManager()
