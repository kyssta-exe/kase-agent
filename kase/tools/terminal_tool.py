"""Terminal execution and process management."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, Optional
from kase.tools.registry import registry, tool_error, tool_result


_ACTIVE_SESSIONS: Dict[str, Dict] = {}
_SESSION_LOCK = threading.Lock()


def _run_command(command: str, cwd: str = None, timeout: int = 120) -> dict:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd or os.getcwd(),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout[-100000:] if result.stdout else "",
            "stderr": result.stderr[-50000:] if result.stderr else "",
        }
    except subprocess.TimeoutExpired:
        return {"exit_code": -1, "stdout": "", "stderr": "Command timed out"}
    except Exception as e:
        return {"exit_code": -1, "stdout": "", "stderr": str(e)}


def terminal_tool(args: dict, **kwargs) -> str:
    command = args.get("command", "")
    cwd = args.get("cwd", "") or os.getcwd()
    timeout = min(args.get("timeout", 120), 600)
    description = args.get("description", "")
    is_background = args.get("background", False)
    
    if not command:
        return tool_error("command is required")
    
    if is_background:
        import uuid
        session_id = f"bg_{uuid.uuid4().hex[:12]}"
        t = threading.Thread(
            target=lambda: _ACTIVE_SESSIONS.update({
                session_id: _run_command(command, cwd, timeout)
            }),
            daemon=True,
        )
        t.start()
        return tool_result(session_id=session_id, status="started", message="Background process started")
    
    result = _run_command(command, cwd, timeout)
    
    output = ""
    if result["stdout"]:
        output += result["stdout"]
    if result["stderr"]:
        if output:
            output += "\n--- stderr ---\n"
        output += result["stderr"]
    
    return tool_result(
        exit_code=result["exit_code"],
        output=output[-100000:],
        command=command[:200],
    )


def process_tool(args: dict, **kwargs) -> str:
    action = args.get("action", "list")
    session_id = args.get("session_id", "")
    
    if action == "list":
        with _SESSION_LOCK:
            sessions = list(_ACTIVE_SESSIONS.keys())
        return tool_result(sessions=sessions[-20:], count=len(sessions))
    
    if action == "status" and session_id:
        with _SESSION_LOCK:
            result = _ACTIVE_SESSIONS.get(session_id)
        if result:
            return tool_result(session_id=session_id, status="completed", result=result)
        return tool_result(session_id=session_id, status="running" if session_id.startswith("bg_") else "unknown")
    
    if action == "stop" and session_id:
        with _SESSION_LOCK:
            _ACTIVE_SESSIONS.pop(session_id, None)
        return tool_result(session_id=session_id, status="stopped")
    
    return tool_result(action=action, status="ok")


_DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\s+/\b", r"\bshutdown\b", r"\breboot\b",
    r"\bmkfs\b", r"\bdd\s+if=", r">\s*/dev/sd",
]

registry.register(
    name="terminal",
    toolset="terminal",
    schema={
        "description": "Execute a terminal command and return the output",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to execute"},
                "cwd": {"type": "string", "description": "Working directory"},
                "timeout": {"type": "integer", "description": "Timeout in seconds"},
                "description": {"type": "string", "description": "Description of what the command does"},
                "background": {"type": "boolean", "description": "Run in background"},
            },
            "required": ["command"],
        },
    },
    handler=terminal_tool,
    emoji="⎇",
)

registry.register(
    name="process",
    toolset="terminal",
    schema={
        "description": "Manage terminal processes: list, status, stop",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "status", "stop"]},
                "session_id": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    handler=process_tool,
)
