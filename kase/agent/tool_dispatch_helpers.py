"""Tool dispatch helpers — parallelism gating, multimodal, trajectory."""

import json
import logging
from typing import Any, Dict, List, Optional

from kase.tools.registry import registry, tool_result as mk_result

logger = logging.getLogger(__name__)


_DESTRUCTIVE_TOOLS = {"write_file", "patch", "terminal"}
_IDEMPOTENT_TOOLS = {"read_file", "search_files", "web_search", "web_extract"}


def _is_destructive_command(command: str) -> bool:
    dangerous = ["rm -rf", "mkfs", "dd if=", "> /dev/sd", "shutdown", "reboot"]
    return any(d in command.lower() for d in dangerous)


def _should_parallelize_tool_batch(tool_calls: List[Dict]) -> bool:
    names = [tc.get("function", {}).get("name", "") for tc in tool_calls]

    if any(n in _DESTRUCTIVE_TOOLS for n in names):
        return False

    destructive_count = sum(1 for n in names if n in _DESTRUCTIVE_TOOLS)
    return destructive_count == 0


def _paths_overlap(tool_calls: List[Dict]) -> bool:
    paths = []
    for tc in tool_calls:
        fn = tc.get("function", {})
        raw_args = fn.get("arguments", "{}")
        if isinstance(raw_args, dict):
            args = raw_args
        else:
            args = json.loads(raw_args) if raw_args else {}
        path = args.get("path", args.get("command", ""))
        if path:
            paths.append(path)

    return len(paths) != len(set(paths))


def dispatch_tool_calls(
    tool_calls: List[Dict],
    task_id: str = None,
) -> List[Dict[str, Any]]:
    """Execute tool calls sequentially and return result messages."""
    results = []

    for tc in tool_calls:
        fn = tc.get("function", {})
        name = fn.get("name", "")
        raw_args = fn.get("arguments", "{}")

        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except json.JSONDecodeError:
            args = {"_raw": raw_args}

        tool_id = tc.get("id", f"call_{name}")

        logger.debug("Dispatching tool: %s (args: %s)", name, str(args)[:200])

        result_str = registry.dispatch(name, args, task_id=task_id)

        try:
            result_data = json.loads(result_str)
        except (json.JSONDecodeError, TypeError):
            result_data = {"result": str(result_str)}

        results.append({
            "role": "tool",
            "tool_call_id": tool_id,
            "content": result_str[:100000],
        })

        if "error" in result_data and result_data["error"]:
            logger.warning("Tool %s returned error: %s", name, result_data["error"])

    return results


def normalize_tool_calls(response: Any) -> List[Dict]:
    """Normalize tool calls from various API response formats."""
    if hasattr(response, "tool_calls"):
        calls = response.tool_calls
        if not calls:
            return []
        result = []
        for tc in calls:
            result.append({
                "id": tc.id,
                "type": "function",
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            })
        return result

    if isinstance(response, dict):
        return response.get("tool_calls", [])

    return []
