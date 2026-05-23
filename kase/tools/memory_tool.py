"""Memory persistence tool."""

import json
import os
from pathlib import Path
from kase.tools.registry import registry, tool_error, tool_result


def _get_memory_store() -> dict:
    store_path = Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "memory.json"
    if store_path.exists():
        try:
            return json.loads(store_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_memory_store(data: dict) -> None:
    store_path = Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "memory.json"
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def memory_tool(args: dict, **kwargs) -> str:
    action = args.get("action", "read")
    key = args.get("key", "")
    value = args.get("value", None)
    
    store = _get_memory_store()
    
    if action == "read":
        if key:
            return tool_result(key=key, value=store.get(key))
        return tool_result(memory=store, keys=list(store.keys()))
    
    elif action == "write":
        if not key:
            return tool_error("key is required for write")
        store[key] = value
        _save_memory_store(store)
        return tool_result(success=True, key=key)
    
    elif action == "delete":
        if key and key in store:
            del store[key]
            _save_memory_store(store)
            return tool_result(success=True, key=key)
        return tool_error(f"key not found: {key}")
    
    elif action == "list":
        keys = list(store.keys())
        return tool_result(keys=keys, count=len(keys))
    
    return tool_error(f"Unknown action: {action}")


registry.register(
    name="memory",
    toolset="memory",
    schema={
        "description": "Store and retrieve persistent key-value memories across sessions",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "write", "delete", "list"],
                    "description": "Memory operation",
                },
                "key": {"type": "string", "description": "Memory key"},
                "value": {"description": "Value to store (for write action)"},
            },
            "required": ["action"],
        },
    },
    handler=memory_tool,
    emoji="♡",
)
