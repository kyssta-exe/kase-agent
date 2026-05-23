"""Background skill maintenance — review, archive, lifecycle."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SkillCurator:
    def __init__(self):
        self._kase_home = Path(os.getenv("KASE_HOME", Path.home() / ".kase"))
        self._usage_file = self._kase_home / "skills" / ".usage.json"
        self._archive_dir = self._kase_home / "skills" / ".archive"

    def _load_usage(self) -> Dict[str, Any]:
        if self._usage_file.exists():
            try:
                return json.loads(self._usage_file.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_usage(self, data: dict) -> None:
        self._usage_file.parent.mkdir(parents=True, exist_ok=True)
        self._usage_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def record_usage(self, skill_name: str) -> None:
        usage = self._load_usage()
        entry = usage.setdefault(skill_name, {"use_count": 0, "last_used": None, "state": "active", "pinned": False})
        entry["use_count"] = entry.get("use_count", 0) + 1
        entry["last_used"] = datetime.now().isoformat()
        self._save_usage(usage)

    def archive_skill(self, skill_name: str) -> bool:
        skill_dir = self._kase_home / "skills" / skill_name
        if not skill_dir.exists():
            return False
        self._archive_dir.mkdir(parents=True, exist_ok=True)
        dest = self._archive_dir / skill_name
        skill_dir.rename(dest)
        
        usage = self._load_usage()
        if skill_name in usage:
            usage[skill_name]["state"] = "archived"
            self._save_usage(usage)
        return True

    def restore_skill(self, skill_name: str) -> bool:
        archived = self._archive_dir / skill_name
        if not archived.exists():
            return False
        dest = self._kase_home / "skills" / skill_name
        archived.rename(dest)
        
        usage = self._load_usage()
        if skill_name in usage:
            usage[skill_name]["state"] = "active"
            self._save_usage(usage)
        return True
