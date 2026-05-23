"""Analytics tracker — records every API call for dashboard metrics."""

import json
import logging
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is not None and not isinstance(db_path, Path):
            db_path = Path(str(db_path))
        self._db_path = db_path or Path(
            os.getenv("KASE_HOME", Path.home() / ".kase")
        ) / "analytics.db"
        self._local = threading.local()
        self._lock = threading.Lock()
        self._enabled = True
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
            CREATE TABLE IF NOT EXISTS api_calls (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                session_id TEXT,
                model TEXT,
                provider TEXT,
                task_type TEXT,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0,
                duration_ms REAL DEFAULT 0,
                success INTEGER DEFAULT 1,
                error TEXT,
                tool_calls INTEGER DEFAULT 0,
                fallback_used INTEGER DEFAULT 0
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_timestamp
            ON api_calls(timestamp)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_api_session
            ON api_calls(session_id)
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                model TEXT,
                provider TEXT,
                message_count INTEGER DEFAULT 0,
                total_tokens INTEGER DEFAULT 0
            )
        """)
        conn.commit()

    def record_call(self, session_id: str, model: str, provider: str,
                    task_type: str = "agentic", prompt_tokens: int = 0,
                    completion_tokens: int = 0, duration_ms: float = 0,
                    success: bool = True, error: str = "",
                    tool_calls: int = 0, fallback_used: bool = False) -> str:
        if not self._enabled:
            return ""
        call_id = f"call_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO api_calls (id, timestamp, session_id, model, provider, "
            "task_type, prompt_tokens, completion_tokens, total_tokens, "
            "duration_ms, success, error, tool_calls, fallback_used) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (call_id, now, session_id, model, provider, task_type,
             prompt_tokens, completion_tokens, prompt_tokens + completion_tokens,
             duration_ms, 1 if success else 0, error or "",
             tool_calls, 1 if fallback_used else 0),
        )
        conn.commit()
        return call_id

    def get_overview(self, hours: int = 24) -> Dict:
        conn = self._get_conn()
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        total_calls = conn.execute(
            "SELECT COUNT(*) FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchone()[0]
        total_tokens = conn.execute(
            "SELECT COALESCE(SUM(total_tokens), 0) FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchone()[0]
        prompt_tokens = conn.execute(
            "SELECT COALESCE(SUM(prompt_tokens), 0) FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchone()[0]
        completion_tokens = conn.execute(
            "SELECT COALESCE(SUM(completion_tokens), 0) FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchone()[0]
        errors = conn.execute(
            "SELECT COUNT(*) FROM api_calls WHERE timestamp >= ? AND success = 0",
            (since,),
        ).fetchone()[0]
        unique_models = conn.execute(
            "SELECT DISTINCT model FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchall()
        models_used = [r["model"] for r in unique_models]
        unique_sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchone()[0]
        avg_duration = conn.execute(
            "SELECT COALESCE(AVG(duration_ms), 0) FROM api_calls WHERE timestamp >= ?",
            (since,),
        ).fetchone()[0]
        return {
            "total_calls": total_calls,
            "total_tokens": total_tokens,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "errors": errors,
            "models_used": models_used,
            "unique_sessions": unique_sessions,
            "avg_duration_ms": round(avg_duration, 2),
            "time_period_hours": hours,
        }

    def get_token_timeline(self, hours: int = 168, interval: str = "hour") -> List[Dict]:
        conn = self._get_conn()
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        if interval == "hour":
            fmt = "%Y-%m-%d %H:00:00"
        else:
            fmt = "%Y-%m-%d"
        rows = conn.execute(
            "SELECT substr(timestamp, 1, 13) || ':00:00' as bucket, "
            "COUNT(*) as calls, SUM(total_tokens) as tokens, "
            "SUM(prompt_tokens) as prompt, SUM(completion_tokens) as completion "
            "FROM api_calls WHERE timestamp >= ? "
            "GROUP BY bucket ORDER BY bucket",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_model_breakdown(self, hours: int = 168) -> List[Dict]:
        conn = self._get_conn()
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        rows = conn.execute(
            "SELECT model, provider, COUNT(*) as calls, "
            "SUM(total_tokens) as tokens, "
            "AVG(duration_ms) as avg_duration, "
            "SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as errors "
            "FROM api_calls WHERE timestamp >= ? "
            "GROUP BY model, provider ORDER BY calls DESC",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_task_breakdown(self, hours: int = 168) -> List[Dict]:
        conn = self._get_conn()
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        rows = conn.execute(
            "SELECT task_type, COUNT(*) as calls, "
            "SUM(total_tokens) as tokens, "
            "AVG(duration_ms) as avg_duration "
            "FROM api_calls WHERE timestamp >= ? "
            "GROUP BY task_type ORDER BY calls DESC",
            (since,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_calls(self, limit: int = 50) -> List[Dict]:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM api_calls ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_all_time_stats(self) -> Dict:
        conn = self._get_conn()
        total_calls = conn.execute("SELECT COUNT(*) FROM api_calls").fetchone()[0]
        total_tokens = conn.execute(
            "SELECT COALESCE(SUM(total_tokens), 0) FROM api_calls"
        ).fetchone()[0]
        first_call = conn.execute(
            "SELECT MIN(timestamp) FROM api_calls"
        ).fetchone()[0]
        return {
            "total_calls_all_time": total_calls,
            "total_tokens_all_time": total_tokens,
            "first_call": first_call or "",
        }

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
