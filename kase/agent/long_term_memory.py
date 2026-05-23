"""Long-term memory — auto-learns from conversations, persists forever."""

import json
import logging
import os
import re
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


MEMORY_TYPES = {"fact", "preference", "knowledge", "project", "user_info", "workflow"}


@dataclass
class MemoryEntry:
    id: str = ""
    memory_type: str = "fact"
    content: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""
    confidence: float = 1.0
    created_at: str = ""
    updated_at: str = ""
    access_count: int = 0
    last_accessed: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.memory_type,
            "content": self.content,
            "tags": self.tags,
            "source": self.source,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
        }


_EXTRACTION_PATTERNS = {
    "preference": [
        r"(?:i|my|the user)\s+(?:like|love|prefer|enjoy|hate|dislike)\s+(\w+(?: \w+){0,5})",
        r"(?:i|my|the user)\s+(?:am|'m)\s+(?:a|an)\s+(\w+(?: \w+){0,3})\s+(?:person|developer|engineer|designer)",
        r"(?:my|the user's)\s+favorite\s+(\w+(?: \w+){0,3})\s+is\s+(\w+(?: \w+){0,3})",
        r"(?:i|we)\s+(?:usually|always|typically)\s+(\w+(?: \w+){0,5})",
    ],
    "fact": [
        r"(?:the\s+)?(\w+(?: \w+){0,3})\s+is\s+(?:a|an|the)\s+(\w+(?: \w+){0,5})",
        r"(?:i\s+)?work\s+(?:at|for)\s+(\w+(?: \w+){0,3})",
        r"(?:i\s+)?(?:have|has)\s+(\d+)\s+years?\s+of\s+experience",
        r"(?:the\s+)?project\s+\w+\s+uses\s+(\w+(?: \w+){0,3})",
    ],
    "project": [
        r"(?:the\s+)?project\s+is\s+(?:called|named)\s+(\w+(?: \w+){0,3})",
        r"(?:working|work)\s+on\s+(?:a|the)\s+(\w+(?: \w+){0,3})\s+project",
        r"(?:repo|repository)\s+(?:is\s+)?(?:at|:)\s+(\S+)",
    ],
}


class LongTermMemory:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is not None and not isinstance(db_path, Path):
            db_path = Path(str(db_path))
        self._db_path = db_path or Path(
            os.getenv("KASE_HOME", Path.home() / ".kase")
        ) / "long_term_memory.db"
        self._local = threading.local()
        self._lock = threading.Lock()
        self._auto_extract_enabled = True
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(str(self._db_path))
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                memory_type TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '[]',
                source TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                created_at TEXT,
                updated_at TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_type
            ON memories(memory_type)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_content
            ON memories(content)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_tags (
                id TEXT PRIMARY KEY,
                tag TEXT NOT NULL,
                memory_id TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_tag
            ON memory_tags(tag)
        """)
        conn.commit()

    def store(self, content: str, memory_type: str = "fact",
              tags: Optional[List[str]] = None,
              source: str = "", confidence: float = 1.0) -> str:
        existing = self._find_exact_match(content, memory_type)
        if existing:
            self._update_entry(existing["id"], confidence=confidence, source=source)
            return existing["id"]

        entry_id = f"mem_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [])
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO memories (id, memory_type, content, tags, source, "
            "confidence, created_at, updated_at, access_count, last_accessed) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)",
            (entry_id, memory_type, content, tags_json, source,
             confidence, now, now, now),
        )
        for tag in (tags or []):
            tag_id = f"tag_{uuid.uuid4().hex[:8]}"
            conn.execute(
                "INSERT INTO memory_tags (id, tag, memory_id) VALUES (?, ?, ?)",
                (tag_id, tag.lower().strip(), entry_id),
            )
        conn.commit()
        logger.debug("Stored memory: %s [%s]", content[:80], memory_type)
        return entry_id

    def _find_exact_match(self, content: str, memory_type: str) -> Optional[Dict]:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM memories WHERE content = ? AND memory_type = ?",
            (content, memory_type),
        ).fetchone()
        return dict(row) if row else None

    def _update_entry(self, entry_id: str, **kwargs) -> None:
        now = datetime.now().isoformat()
        updates = {"updated_at": now}
        updates.update(kwargs)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [entry_id]
        conn = self._get_conn()
        conn.execute(
            f"UPDATE memories SET {set_clause} WHERE id = ?", values
        )
        conn.commit()

    def recall(self, query: str, memory_type: Optional[str] = None,
               limit: int = 10, min_confidence: float = 0.3) -> List[Dict]:
        conn = self._get_conn()
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        sql = "SELECT * FROM memories WHERE confidence >= ?"
        params: List[Any] = [min_confidence]
        if memory_type:
            sql += " AND memory_type = ?"
            params.append(memory_type)
        rows = conn.execute(sql + " ORDER BY confidence DESC, access_count DESC LIMIT ?",
                            params + [limit * 3]).fetchall()

        scored = []
        for row in rows:
            entry = dict(row)
            try:
                tags = json.loads(entry.get("tags", "[]"))
            except (json.JSONDecodeError, TypeError):
                tags = []
            entry["tags"] = tags

            content_lower = (entry.get("content", "") or "").lower()
            content_words = set(re.findall(r'\w+', content_lower))

            score = 0.0
            if query_lower in content_lower:
                score += 3.0
            word_overlap = query_words & content_words
            if word_overlap:
                score += len(word_overlap) * 0.5
            tag_overlap = set(t.lower() for t in tags) & query_words
            if tag_overlap:
                score += len(tag_overlap) * 1.0

            score *= entry.get("confidence", 0.5)

            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda x: -x[0])
        results = [entry for _, entry in scored[:limit]]

        for entry in results:
            conn.execute(
                "UPDATE memories SET access_count = access_count + 1, "
                "last_accessed = ? WHERE id = ?",
                (datetime.now().isoformat(), entry["id"]),
            )
        conn.commit()

        return results

    def extract_from_text(self, text: str, source: str = "conversation") -> List[str]:
        if not self._auto_extract_enabled:
            return []
        extracted_ids = []
        text_lower = text.lower()

        for mem_type, patterns in _EXTRACTION_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        content = " ".join(m for m in match if m)
                    else:
                        content = str(match)
                    content = content.strip()
                    if len(content) > 3 and content not in ("", "the", "a", "an"):
                        tags = [mem_type]
                        if any(w in content for w in ("python", "javascript", "rust", "go", "typescript")):
                            tags.append("programming_language")
                        if any(w in content for w in ("project", "repo", "app", "website")):
                            tags.append("project")
                        entry_id = self.store(
                            content=content,
                            memory_type=mem_type,
                            tags=tags,
                            source=source,
                            confidence=0.5,
                        )
                        extracted_ids.append(entry_id)
        return extracted_ids

    def extract_from_messages(self, messages: List[Dict],
                               source: str = "conversation") -> List[str]:
        extracted_ids = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                ids = self.extract_from_text(content, source)
                extracted_ids.extend(ids)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        ids = self.extract_from_text(part.get("text", ""), source)
                        extracted_ids.extend(ids)
        return extracted_ids

    def delete(self, memory_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.execute("DELETE FROM memory_tags WHERE memory_id = ?", (memory_id,))
        conn.commit()
        return cursor.rowcount > 0

    def delete_by_content(self, content: str, memory_type: Optional[str] = None) -> int:
        conn = self._get_conn()
        if memory_type:
            cursor = conn.execute(
                "DELETE FROM memories WHERE content LIKE ? AND memory_type = ?",
                (f"%{content}%", memory_type),
            )
        else:
            cursor = conn.execute(
                "DELETE FROM memories WHERE content LIKE ?",
                (f"%{content}%",),
            )
        conn.commit()
        return cursor.rowcount

    def delete_by_type(self, memory_type: str) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM memories WHERE memory_type = ?", (memory_type,)
        )
        conn.commit()
        return cursor.rowcount

    def clear_all(self) -> int:
        conn = self._get_conn()
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM memory_tags")
        conn.commit()
        return count

    def get_all(self, memory_type: Optional[str] = None,
                limit: int = 100, offset: int = 0) -> List[Dict]:
        conn = self._get_conn()
        if memory_type:
            rows = conn.execute(
                "SELECT * FROM memories WHERE memory_type = ? "
                "ORDER BY confidence DESC, created_at DESC LIMIT ? OFFSET ?",
                (memory_type, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY confidence DESC, "
                "created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        results = []
        for row in rows:
            entry = dict(row)
            try:
                entry["tags"] = json.loads(entry.get("tags", "[]"))
            except (json.JSONDecodeError, TypeError):
                entry["tags"] = []
            results.append(entry)
        return results

    def get_stats(self) -> Dict:
        conn = self._get_conn()
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_type = conn.execute(
            "SELECT memory_type, COUNT(*) as cnt FROM memories GROUP BY memory_type"
        ).fetchall()
        tags = conn.execute(
            "SELECT tag, COUNT(*) as cnt FROM memory_tags GROUP BY tag ORDER BY cnt DESC LIMIT 20"
        ).fetchall()
        return {
            "total_facts": total,
            "total_preferences": sum(r["cnt"] for r in by_type if r["memory_type"] == "preference"),
            "total_knowledge": sum(r["cnt"] for r in by_type if r["memory_type"] == "knowledge"),
            "total_projects": sum(r["cnt"] for r in by_type if r["memory_type"] == "project"),
            "by_type": {r["memory_type"]: r["cnt"] for r in by_type},
            "top_tags": [{"tag": r["tag"], "count": r["cnt"]} for r in tags],
        }

    def search_by_tag(self, tag: str, limit: int = 50) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT m.* FROM memories m "
            "JOIN memory_tags t ON m.id = t.memory_id "
            "WHERE t.tag = ? ORDER BY m.confidence DESC LIMIT ?",
            (tag.lower().strip(), limit),
        ).fetchall()
        results = []
        for row in rows:
            entry = dict(row)
            try:
                entry["tags"] = json.loads(entry.get("tags", "[]"))
            except (json.JSONDecodeError, TypeError):
                entry["tags"] = []
            results.append(entry)
        return results

    def set_auto_extract(self, enabled: bool) -> None:
        self._auto_extract_enabled = enabled

    def build_context_block(self, query: str = "", max_items: int = 8) -> str:
        if not query:
            return ""
        results = self.recall(query, limit=max_items)
        if not results:
            return ""
        lines = ["<remembered>"]
        for r in results:
            mtype = r.get("memory_type", "fact")
            content = r.get("content", "")
            lines.append(f"  [{mtype}] {content}")
        lines.append("</remembered>")
        return "\n".join(lines)
