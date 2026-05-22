"""Silent background auto-updater for Kase.

Checks for updates periodically and installs them without
user interaction.  Runs as a daemon thread so it never blocks
shutdown.  Update results are logged and persisted in
``KASE_HOME/.auto_update.json``.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from kase_cli.banner import check_for_updates

logger = logging.getLogger(__name__)

_STATE_FILE = ".auto_update.json"
_MIN_INTERVAL_SECONDS = 300  # 5 min floor

# Resolved once so subprocess calls stay fast
_KASE_BIN: Optional[str] = None


def _resolve_kase_bin() -> str:
    global _KASE_BIN
    if _KASE_BIN is not None:
        return _KASE_BIN
    candidate = shutil.which("kase")
    if candidate:
        _KASE_BIN = candidate
    else:
        _KASE_BIN = os.path.join(
            os.path.dirname(sys.executable), "kase"
        )
        if not os.path.isfile(_KASE_BIN):
            _KASE_BIN = sys.executable
    return _KASE_BIN


class AutoUpdater:
    """Periodic silent auto-updater.

    Starts a daemon thread that checks for new versions every
    *interval_hours* and runs ``kase update --yes`` when one is
    found.  The running process keeps the old code; the update
    takes effect the next time Kase is launched (CLI) or after a
    gateway restart.
    """

    def __init__(self, interval_hours: int = 1, silent: bool = True) -> None:
        self._interval = max(interval_hours * 3600, _MIN_INTERVAL_SECONDS)
        self._silent = silent
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._update_applied = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._run_loop,
            name="kase-auto-updater",
            daemon=True,
        )
        self._thread.start()
        logger.debug("Auto-updater started (interval=%ds)", self._interval)

    def stop(self) -> None:
        self._stop_event.set()

    @property
    def update_applied(self) -> bool:
        return self._update_applied

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run_loop(self) -> None:
        state = self._read_state()
        last_check = state.get("last_check", 0.0)

        while not self._stop_event.is_set():
            now = time.time()
            if now - last_check >= self._interval:
                self._check_and_update()
                last_check = now
                self._write_state({"last_check": now})
            self._stop_event.wait(timeout=60)

    def _check_and_update(self) -> None:
        try:
            behind = check_for_updates()
            if behind is None or behind == 0:
                return
            logger.info("Update available (%s commits behind)", behind)
            self._apply_update()
            self._update_applied = True
            marker = Path(os.environ.get("KASE_HOME", Path.home() / ".kase"))
            (marker / ".update_applied").write_text(
                json.dumps({"at": time.time(), "behind": behind})
            )
            logger.info("Auto-update applied successfully")
        except Exception:
            logger.exception("Auto-update failed")

    def _apply_update(self) -> None:
        kase = _resolve_kase_bin()
        if kase == sys.executable:
            argv = [kase, "-m", "kase_cli.main", "update", "--yes"]
        else:
            argv = [kase, "update", "--yes"]

        kwargs: dict = {}
        if self._silent:
            kwargs["stdout"] = subprocess.DEVNULL
            kwargs["stderr"] = subprocess.DEVNULL

        result = subprocess.run(argv, check=False, **kwargs)
        if result.returncode != 0:
            raise RuntimeError(f"Auto-update exited with code {result.returncode}")

    def _read_state(self) -> dict:
        home = Path(os.environ.get("KASE_HOME", Path.home() / ".kase"))
        p = home / _STATE_FILE
        try:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def _write_state(self, state: dict) -> None:
        home = Path(os.environ.get("KASE_HOME", Path.home() / ".kase"))
        p = home / _STATE_FILE
        try:
            p.write_text(json.dumps(state), encoding="utf-8")
        except Exception:
            pass


# ------------------------------------------------------------------
# Global singleton helpers — call from CLI / gateway startup
# ------------------------------------------------------------------

_updater: Optional[AutoUpdater] = None


def start_auto_updater(interval_hours: int = 1, silent: bool = True) -> AutoUpdater:
    global _updater
    if _updater is None:
        _updater = AutoUpdater(interval_hours=interval_hours, silent=silent)
        _updater.start()
    return _updater


def stop_auto_updater() -> None:
    global _updater
    if _updater is not None:
        _updater.stop()
        _updater = None
