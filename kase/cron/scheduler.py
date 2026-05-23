"""Cron scheduler — tick loop for running scheduled jobs."""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CronScheduler:
    def __init__(self):
        self._jobs_file = Path(os.getenv("KASE_HOME", Path.home() / ".kase")) / "cron" / "jobs.json"
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def _load_jobs(self) -> List[Dict]:
        if self._jobs_file.exists():
            try:
                return json.loads(self._jobs_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    def _save_jobs(self, jobs: List[Dict]) -> None:
        self._jobs_file.parent.mkdir(parents=True, exist_ok=True)
        self._jobs_file.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_job(self, schedule: str, command: str, **kwargs) -> str:
        import uuid
        job = {
            "id": f"cron_{uuid.uuid4().hex[:12]}",
            "schedule": schedule,
            "command": command,
            "created_at": datetime.now().isoformat(),
            "paused": False,
            "last_run": None,
            "run_count": 0,
            **kwargs,
        }
        jobs = self._load_jobs()
        jobs.append(job)
        self._save_jobs(jobs)
        return job["id"]

    def remove_job(self, job_id: str) -> bool:
        jobs = self._load_jobs()
        filtered = [j for j in jobs if j.get("id") != job_id]
        if len(filtered) != len(jobs):
            self._save_jobs(filtered)
            return True
        return False

    def list_jobs(self) -> List[Dict]:
        return self._load_jobs()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._thread.start()
        logger.info("Cron scheduler started")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Cron scheduler stopped")

    def _tick_loop(self) -> None:
        while self._running:
            try:
                self._tick()
            except Exception as e:
                logger.error("Cron tick error: %s", e)
            time.sleep(60)

    def _tick(self) -> None:
        jobs = self._load_jobs()
        now = datetime.now()
        
        for job in jobs:
            if job.get("paused"):
                continue
            if self._is_due(job, now):
                self._execute_job(job)

    def _is_due(self, job: Dict, now: datetime) -> bool:
        last_run = job.get("last_run")
        schedule = job.get("schedule", "")
        
        if not last_run:
            return True
        
        try:
            last = datetime.fromisoformat(last_run)
            
            if schedule.endswith("m"):
                minutes = int(schedule[:-1])
                return (now - last).total_seconds() >= minutes * 60
            elif schedule.endswith("h"):
                hours = int(schedule[:-1])
                return (now - last).total_seconds() >= hours * 3600
            elif schedule.endswith("d"):
                days = int(schedule[:-1])
                return (now - last).total_seconds() >= days * 86400
        except Exception:
            pass
        
        return False

    def _execute_job(self, job: Dict) -> None:
        command = job.get("command", "")
        if not command:
            return
        
        logger.info("Executing cron job %s: %s", job.get("id"), command[:100])
        
        try:
            import subprocess
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=300)
            
            jobs = self._load_jobs()
            for j in jobs:
                if j.get("id") == job.get("id"):
                    j["last_run"] = datetime.now().isoformat()
                    j["run_count"] = (j.get("run_count", 0) or 0) + 1
                    j["last_output"] = result.stdout[-1000:] if result.stdout else ""
                    j["last_error"] = result.stderr[-500:] if result.stderr else ""
                    j["last_exit_code"] = result.returncode
                    break
            self._save_jobs(jobs)
            
        except Exception as e:
            logger.warning("Cron job %s failed: %s", job.get("id"), e)
