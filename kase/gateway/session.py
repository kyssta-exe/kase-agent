"""Gateway session management."""

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class SessionSource:
    platform: str = ""
    chat_id: str = ""
    chat_name: str = ""
    chat_type: str = ""
    user_id: str = ""
    user_name: str = ""
    message_id: str = ""


@dataclass
class SessionContext:
    source: SessionSource = field(default_factory=SessionSource)
    session_key: str = ""
    connected_platforms: List[str] = field(default_factory=list)


class SessionStore:
    def __init__(self, store_path: Optional[Path] = None):
        self._store_path = store_path or Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "gateway_sessions.json"
        self._sessions: Dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self._store_path.exists():
            try:
                self._sessions = json.loads(self._store_path.read_text(encoding="utf-8"))
            except Exception:
                self._sessions = {}

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_text(json.dumps(self._sessions, indent=2, ensure_ascii=False), encoding="utf-8")

    def get_session(self, key: str) -> Optional[dict]:
        return self._sessions.get(key)

    def set_session(self, key: str, data: dict) -> None:
        self._sessions[key] = data
        self._save()

    def delete_session(self, key: str) -> None:
        self._sessions.pop(key, None)
        self._save()

    def list_sessions(self) -> List[str]:
        return list(self._sessions.keys())


def make_session_key(source: SessionSource) -> str:
    raw = f"{source.platform}:{source.chat_id}:{source.user_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]
