"""SQLite-backed Kanban board for multi-agent work coordination."""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KanbanBoard:
    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path or Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "kanban.db"
        self._local = threading.local()
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
            CREATE TABLE IF NOT EXISTS cards (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'todo',
                assignee TEXT,
                board TEXT DEFAULT 'default',
                tenant TEXT DEFAULT 'default',
                priority INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                blocked BOOLEAN DEFAULT 0,
                failure_count INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                card_id TEXT,
                author TEXT,
                body TEXT,
                created_at TEXT,
                FOREIGN KEY (card_id) REFERENCES cards(id)
            )
        """)
        conn.commit()

    def create_card(self, title: str, description: str = "", board: str = "default",
                    tenant: str = "default", priority: int = 0) -> str:
        import uuid
        card_id = f"card_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO cards (id, title, description, status, board, tenant, priority, created_at, updated_at) "
            "VALUES (?, ?, ?, 'todo', ?, ?, ?, ?, ?)",
            (card_id, title, description, board, tenant, priority, now, now),
        )
        conn.commit()
        return card_id

    def list_cards(self, board: str = "default", status: str = "") -> List[Dict]:
        conn = self._get_conn()
        query = "SELECT * FROM cards WHERE board = ?"
        params = [board]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY priority DESC, created_at DESC"
        
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def update_card(self, card_id: str, **kwargs) -> bool:
        allowed = {"title", "description", "status", "assignee", "priority", "blocked", "failure_count"}
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return False
        
        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [card_id]
        
        conn = self._get_conn()
        cursor = conn.execute(f"UPDATE cards SET {set_clause} WHERE id = ?", values)
        conn.commit()
        return cursor.rowcount > 0

    def add_comment(self, card_id: str, author: str, body: str) -> str:
        import uuid
        comment_id = f"cmt_{uuid.uuid4().hex[:8]}"
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO comments (id, card_id, author, body, created_at) VALUES (?, ?, ?, ?, ?)",
            (comment_id, card_id, author, body, now),
        )
        conn.commit()
        return comment_id

    def get_comments(self, card_id: str) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM comments WHERE card_id = ? ORDER BY created_at", (card_id,)
        ).fetchall()
        return [dict(row) for row in rows]
