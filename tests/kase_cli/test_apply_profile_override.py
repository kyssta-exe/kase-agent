"""Regression tests for _apply_profile_override KASE_HOME guard (issue #22502).

When KASE_HOME is set to the kase root (e.g. systemd hardcodes
KASE_HOME=/root/.kase), _apply_profile_override must still read
active_profile and update KASE_HOME to the profile directory.

When KASE_HOME is already a profile directory (.../profiles/<name>),
_apply_profile_override must trust it and return without re-reading
active_profile (child-process inheritance contract).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


def _run_apply_profile_override(
    tmp_path, monkeypatch, *, hermes_home: str | None, active_profile: str | None,
    argv: list[str] | None = None,
):
    """Run _apply_profile_override in isolation.

    Returns the value of os.environ["KASE_HOME"] after the call,
    or None if unset.
    """
    hermes_root = tmp_path / ".kase"
    hermes_root.mkdir(parents=True, exist_ok=True)

    if active_profile is not None:
        (hermes_root / "active_profile").write_text(active_profile)

    if active_profile and active_profile != "default":
        (hermes_root / "profiles" / active_profile).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    if hermes_home is not None:
        monkeypatch.setenv("KASE_HOME", hermes_home)
    else:
        monkeypatch.delenv("KASE_HOME", raising=False)

    monkeypatch.setattr(sys, "argv", argv or ["kase", "gateway", "start"])

    from kase_cli.main import _apply_profile_override
    _apply_profile_override()

    return os.environ.get("KASE_HOME")


class TestApplyProfileOverrideHermesHomeGuard:
    """Regression guard for issue #22502.

    Verifies that KASE_HOME pointing to the kase root does NOT suppress
    the active_profile check, while KASE_HOME already pointing to a
    profile directory IS trusted as-is.
    """

    def test_kase_home_at_root_with_active_profile_is_redirected(
        self, tmp_path, monkeypatch
    ):
        """KASE_HOME=/root/.kase + active_profile=coder must redirect
        KASE_HOME to .../profiles/coder.

        Bug scenario from #22502: systemd sets KASE_HOME to the kase root
        and the user switches to a profile via `kase profile use`.
        Before the fix, the guard returned early and active_profile was ignored.
        """
        hermes_root = tmp_path / ".kase"
        hermes_root.mkdir(parents=True, exist_ok=True)

        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=str(hermes_root),
            active_profile="coder",
        )

        assert result is not None, "KASE_HOME must be set after profile redirect"
        assert "profiles" in result, (
            f"Expected KASE_HOME to point into profiles/ dir, got: {result!r}"
        )
        assert result.endswith("coder"), (
            f"Expected KASE_HOME to end with 'coder', got: {result!r}"
        )

    def test_kase_home_already_profile_dir_is_trusted(self, tmp_path, monkeypatch):
        """KASE_HOME=.../profiles/coder must not be overridden even when
        active_profile says something different.

        Preserves the child-process inheritance contract: a subprocess spawned
        with KASE_HOME already set to a specific profile must stay in that
        profile.
        """
        hermes_root = tmp_path / ".kase"
        profile_dir = hermes_root / "profiles" / "coder"
        profile_dir.mkdir(parents=True, exist_ok=True)

        (hermes_root / "active_profile").write_text("other")

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("KASE_HOME", str(profile_dir))
        monkeypatch.setattr(sys, "argv", ["kase", "gateway", "start"])

        from kase_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("KASE_HOME") == str(profile_dir), (
            "KASE_HOME must remain unchanged when already pointing to a profile dir"
        )

    def test_kase_home_unset_reads_active_profile(self, tmp_path, monkeypatch):
        """Classic case: KASE_HOME unset + active_profile=coder must set
        KASE_HOME to the profile directory (existing behaviour must not regress).
        """
        result = _run_apply_profile_override(
            tmp_path,
            monkeypatch,
            hermes_home=None,
            active_profile="coder",
        )

        assert result is not None
        assert "coder" in result

    def test_kase_home_unset_default_profile_no_redirect(self, tmp_path, monkeypatch):
        """active_profile=default must not redirect KASE_HOME."""
        hermes_root = tmp_path / ".kase"
        hermes_root.mkdir(parents=True, exist_ok=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.delenv("KASE_HOME", raising=False)
        monkeypatch.setattr(sys, "argv", ["kase", "gateway", "start"])
        (hermes_root / "active_profile").write_text("default")

        from kase_cli.main import _apply_profile_override
        _apply_profile_override()

        assert os.environ.get("KASE_HOME") is None
