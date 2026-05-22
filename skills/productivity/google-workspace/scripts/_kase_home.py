"""Resolve KASE_HOME for standalone skill scripts.

Skill scripts may run outside the Kase process (e.g. system Python,
nix env, CI) where ``kase_constants`` is not importable.  This module
provides the same ``get_kase_home()`` and ``display_kase_home()``
contracts as ``kase_constants`` without requiring it on ``sys.path``.

When ``kase_constants`` IS available it is used directly so that any
future enhancements (profile resolution, Docker detection, etc.) are
picked up automatically.  The fallback path replicates the core logic
from ``kase_constants.py`` using only the stdlib.

All scripts under ``google-workspace/scripts/`` should import from here
instead of duplicating the ``KASE_HOME = Path(os.getenv(...))`` pattern.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from kase_constants import display_kase_home as display_kase_home
    from kase_constants import get_kase_home as get_kase_home
except (ModuleNotFoundError, ImportError):

    def get_kase_home() -> Path:
        """Return the Kase home directory (default: ~/.kase).

        Mirrors ``kase_constants.get_kase_home()``."""
        val = os.environ.get("KASE_HOME", "").strip()
        return Path(val) if val else Path.home() / ".kase"

    def display_kase_home() -> str:
        """Return a user-friendly ``~/``-shortened display string.

        Mirrors ``kase_constants.display_kase_home()``."""
        home = get_kase_home()
        try:
            return "~/" + str(home.relative_to(Path.home()))
        except ValueError:
            return str(home)
