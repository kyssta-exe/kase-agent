"""Dangerous command detection and approval system."""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

_HARDLINE_PATTERNS = [
    r"\brm\s+-rf\s+/\s*$",
    r"\brm\s+-rf\s+/\s+--no-preserve-root\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bpoweroff\b",
    r"\bmkfs\b",
    r"\bdd\s+if=.*\s+of=/dev/sd",
    r">\s*/dev/sd",
]

_DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bchmod\s+777\b",
    r"\bcurl\b.*\|\s*(?:bash|sh|zsh)",
    r"\bwget\b.*\|\s*(?:bash|sh|zsh)",
    r"chown\s",
    r"\bkill\s+-9\b",
    r":\s*!.*\bsudo\b",
]

_APPROVAL_STATE: dict = {}
_APPROVAL_FILE = Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "approvals.json"


def _load_approvals() -> dict:
    if _APPROVAL_FILE.exists():
        try:
            return json.loads(_APPROVAL_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_approvals(data: dict) -> None:
    _APPROVAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    _APPROVAL_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def check_command_safety(command: str) -> dict:
    for pattern in _HARDLINE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {"safe": False, "level": "hardline", "reason": f"Command matches hardline pattern: {pattern}"}
    
    for pattern in _DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return {"safe": False, "level": "dangerous", "reason": f"Command matches dangerous pattern: {pattern}"}
    
    return {"safe": True, "level": "safe", "reason": ""}


def is_command_approved(command: str, session_id: str = "default") -> bool:
    approvals = _load_approvals()
    session_approvals = approvals.get(session_id, {})
    return command in session_approvals


def approve_command(command: str, session_id: str = "default") -> None:
    approvals = _load_approvals()
    session_approvals = approvals.setdefault(session_id, {})
    session_approvals[command] = True
    _save_approvals(approvals)


def request_approval(command: str) -> Optional[bool]:
    safety = check_command_safety(command)
    if safety["safe"]:
        return True
    if safety["level"] == "hardline":
        return False
    print(f"\n  ⚠ Dangerous command detected:")
    print(f"    {command}")
    print(f"    Reason: {safety['reason']}")
    if not sys.stdin.isatty():
        return False
    try:
        response = input("  Approve? (y/N): ").strip().lower()
        return response in ("y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False
