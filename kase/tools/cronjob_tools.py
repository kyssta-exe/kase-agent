"""Cron job scheduling tool."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from kase.tools.registry import registry, tool_error, tool_result


_JOBS_FILE = Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "cron" / "jobs.json"


def _load_jobs() -> list:
    if _JOBS_FILE.exists():
        try:
            return json.loads(_JOBS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_jobs(jobs: list) -> None:
    _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _JOBS_FILE.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")


def cronjob_tool(args: dict, **kwargs) -> str:
    action = args.get("action", "list")
    job_id = args.get("job_id", "")
    schedule = args.get("schedule", "")
    command = args.get("command", "")
    
    jobs = _load_jobs()
    
    if action == "list":
        return tool_result(jobs=jobs, count=len(jobs))
    
    if action == "add":
        if not schedule or not command:
            return tool_error("schedule and command are required")
        new_job = {
            "id": f"job_{len(jobs)}_{int(datetime.now().timestamp())}",
            "schedule": schedule,
            "command": command,
            "created_at": datetime.now().isoformat(),
            "paused": False,
        }
        jobs.append(new_job)
        _save_jobs(jobs)
        return tool_result(success=True, job=new_job)
    
    if action == "remove":
        jobs = [j for j in jobs if j.get("id") != job_id]
        _save_jobs(jobs)
        return tool_result(success=True, removed=True)
    
    if action == "pause":
        for j in jobs:
            if j.get("id") == job_id:
                j["paused"] = True
        _save_jobs(jobs)
        return tool_result(success=True)
    
    if action == "resume":
        for j in jobs:
            if j.get("id") == job_id:
                j["paused"] = False
        _save_jobs(jobs)
        return tool_result(success=True)
    
    return tool_error(f"Unknown action: {action}")


registry.register(
    name="cronjob",
    toolset="cronjob",
    schema={
        "description": "Schedule, manage, and run cron jobs",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "add", "remove", "pause", "resume"],
                },
                "job_id": {"type": "string"},
                "schedule": {"type": "string", "description": "Cron expression or interval (e.g., '30m', '2h')"},
                "command": {"type": "string", "description": "Command to run"},
            },
            "required": ["action"],
        },
    },
    handler=cronjob_tool,
)
