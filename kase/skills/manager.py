"""Skill discovery, loading, and management."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


SKILL_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class Skill:
    def __init__(self, name: str, path: Path, metadata: dict, content: str):
        self.name = name
        self.path = path
        self.metadata = metadata
        self.content = content

    @property
    def description(self) -> str:
        return self.metadata.get("description", "")

    @property
    def category(self) -> str:
        return self.metadata.get("metadata", {}).get("hermes", {}).get("category", "uncategorized")


class SkillManager:
    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._discovered = False

    def discover_skills(self, skill_dirs: Optional[List[Path]] = None) -> None:
        dirs = skill_dirs or [
            Path(__file__).resolve().parent,
            Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "skills",
        ]
        
        for skill_dir in dirs:
            if not skill_dir.exists():
                continue
            for item in skill_dir.iterdir():
                if item.is_dir():
                    self._load_skill_dir(item)
        
        self._discovered = True

    def _load_skill_dir(self, skill_dir: Path) -> None:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            return
        
        try:
            content = skill_file.read_text(encoding="utf-8")
            metadata = self._parse_frontmatter(content)
            clean_content = SKILL_FRONTMATTER_RE.sub("", content).strip()
            
            name = metadata.get("name", skill_dir.name)
            skill = Skill(name=name, path=skill_dir, metadata=metadata, content=clean_content)
            self._skills[name] = skill
            
            if metadata.get("aliases"):
                for alias in metadata["aliases"]:
                    self._skills[alias] = skill
            
        except Exception as e:
            logger.warning("Failed to load skill from %s: %s", skill_dir, e)

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        import yaml
        m = SKILL_FRONTMATTER_RE.match(content)
        if m:
            try:
                return yaml.safe_load(m.group(1)) or {}
            except Exception:
                pass
        return {}

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list_skills(self, category: str = "") -> List[Skill]:
        if category:
            return [s for s in self._skills.values() if s.category == category]
        return list(set(self._skills.values()))

    def get_categories(self) -> List[str]:
        return list(set(s.category for s in self._skills.values()))


_skill_manager = SkillManager()


def get_skill_manager() -> SkillManager:
    return _skill_manager
