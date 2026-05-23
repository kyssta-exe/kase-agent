"""Task tracking and todo management system."""

import json
import os
from datetime import datetime
from pathlib import Path
from kase.tools.registry import registry, tool_error, tool_result


_TODO_FILE = Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "todos.json"


def _load_todos() -> list:
    if _TODO_FILE.exists():
        try:
            return json.loads(_TODO_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_todos(todos: list) -> None:
    _TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    _TODO_FILE.write_text(json.dumps(todos, indent=2, ensure_ascii=False), encoding="utf-8")


def todo_tool(args: dict, **kwargs) -> str:
    action = args.get("action", "list")
    task = args.get("task", "")
    
    todos = _load_todos()
    
    if action == "list":
        return tool_result(todos=todos[-20:], count=len(todos))
    
    if action == "add":
        if not task:
            return tool_error("task is required")
        entry = {
            "id": f"todo_{len(todos)}_{int(datetime.now().timestamp())}",
            "task": task,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        todos.append(entry)
        _save_todos(todos)
        return tool_result(success=True, todo=entry)
    
    if action == "complete":
        for t in todos:
            if t.get("id") == task or t.get("task") == task:
                t["status"] = "completed"
                t["completed_at"] = datetime.now().isoformat()
                _save_todos(todos)
                return tool_result(success=True)
        return tool_error(f"Todo not found: {task}")
    
    if action == "remove":
        todos = [t for t in todos if t.get("id") != task and t.get("task") != task]
        _save_todos(todos)
        return tool_result(success=True, removed=True)
    
    return tool_error(f"Unknown action: {action}")


registry.register(
    name="todo",
    toolset="todo",
    schema={
        "description": "Manage a todo list for task tracking and planning",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "add", "complete", "remove"],
                    "description": "Action to perform",
                },
                "task": {"type": "string", "description": "Task description or ID"},
            },
            "required": ["action"],
        },
    },
    handler=todo_tool,
    emoji="☐",
)
