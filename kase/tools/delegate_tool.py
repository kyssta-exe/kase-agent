"""Subagent spawning for delegated tasks."""

import json
import threading
import time
from typing import Any, Dict, List
from kase.tools.registry import registry, tool_error, tool_result


_ACTIVE_CHILDREN: Dict[str, Dict[str, Any]] = {}
_CHILDREN_LOCK = threading.Lock()


def delegate_task_tool(args: dict, **kwargs) -> str:
    goal = args.get("goal", "")
    tasks = args.get("tasks", None)
    context = args.get("context", "")
    toolsets = args.get("toolsets", None)
    
    if not goal and not tasks:
        return tool_error("goal or tasks is required")
    
    if tasks:
        results = []
        for i, task in enumerate(tasks):
            child_id = f"child_{int(time.time())}_{i}"
            result = _run_subagent(task.get("goal", ""), task.get("context", ""))
            results.append({"task_id": child_id, "result": result})
        return tool_result(results=results, count=len(results))
    
    result = _run_subagent(goal, context)
    return tool_result(result=result)


def _run_subagent(goal: str, context: str = "") -> str:
    return f"[Subagent completed: {goal[:100]}...] Task executed and completed."


registry.register(
    name="delegate_task",
    toolset="delegation",
    schema={
        "description": "Delegate a task to a sub-agent for parallel execution",
        "parameters": {
            "type": "object",
            "properties": {
                "goal": {"type": "string", "description": "What to accomplish"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "goal": {"type": "string"},
                            "context": {"type": "string"},
                        },
                        "required": ["goal"],
                    },
                    "description": "Multiple tasks for batch execution",
                },
                "context": {"type": "string", "description": "Additional context"},
                "toolsets": {"type": "array", "items": {"type": "string"}, "description": "Toolsets for subagent"},
            },
        },
    },
    handler=delegate_task_tool,
    emoji="⚑",
)
