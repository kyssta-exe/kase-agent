"""Credential pool for managing multiple API credentials."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class CredentialPool:
    def __init__(self, kase_home: Optional[Path] = None):
        self._kase_home = kase_home or Path(os.getenv("KASE_HOME", Path.home() / ".kase"))
        self._credentials: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        auth_file = self._kase_home / "auth.json"
        if auth_file.exists():
            try:
                self._credentials = json.loads(auth_file.read_text(encoding="utf-8"))
            except Exception:
                self._credentials = {}

    def _save(self) -> None:
        self._kase_home.mkdir(parents=True, exist_ok=True)
        auth_file = self._kase_home / "auth.json"
        auth_file.write_text(json.dumps(self._credentials, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_credential(self, provider: str, credential: Dict[str, Any]) -> None:
        if provider not in self._credentials:
            self._credentials[provider] = []
        self._credentials[provider].append(credential)
        self._save()

    def get_credentials(self, provider: str) -> List[Dict[str, Any]]:
        return self._credentials.get(provider, [])

    def get_best_credential(self, provider: str) -> Optional[Dict[str, Any]]:
        creds = self.get_credentials(provider)
        if not creds:
            return None
        for cred in creds:
            if cred.get("active", True):
                return cred
        return creds[0] if creds else None

    def get_api_key(self, env_var: str) -> Optional[str]:
        key = os.getenv(env_var)
        if key:
            return key
        provider = env_var.lower().replace("_api_key", "").replace("_token", "")
        cred = self.get_best_credential(provider)
        if cred:
            return cred.get("api_key") or cred.get("token")
        return None

    def remove_credential(self, provider: str, index: int = 0) -> None:
        if provider in self._credentials and 0 <= index < len(self._credentials[provider]):
            self._credentials[provider].pop(index)
            if not self._credentials[provider]:
                del self._credentials[provider]
            self._save()
