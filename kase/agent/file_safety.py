"""Security rules for file read/write operations."""

import os
from pathlib import Path
from typing import Optional


def get_kase_paths() -> tuple[Path, Path]:
    try:
        from kase.utils import get_kase_home
        home = get_kase_home()
    except Exception:
        home = Path.home() / ".kase"
    return home, home


_WRITE_DENIED_PATHS = {
    ".ssh/authorized_keys", ".ssh/id_rsa", ".ssh/id_ed25519", ".ssh/config",
    ".bashrc", ".zshrc", ".profile", ".bash_profile", ".zprofile",
    ".netrc", ".pgpass", ".npmrc", ".pypirc",
}

_WRITE_DENIED_PREFIXES = {
    ".ssh", ".aws", ".gnupg", ".kube", ".docker", ".azure",
}


def is_write_denied(path: str) -> bool:
    home = Path.home().resolve()
    resolved = Path(path).expanduser().resolve()
    
    for denied in _WRITE_DENIED_PATHS:
        if resolved == (home / denied).resolve():
            return True
    
    for prefix in _WRITE_DENIED_PREFIXES:
        try:
            resolved.relative_to(home / prefix)
            return True
        except ValueError:
            continue
    
    kase_home, _ = get_kase_paths()
    control_files = {"auth.json", "config.yaml", ".env"}
    for cf in control_files:
        if resolved == (kase_home / cf).resolve():
            return True
    
    return False


def get_read_block_error(path: str) -> Optional[str]:
    kase_home, _ = get_kase_paths()
    resolved = Path(path).expanduser().resolve()
    
    blocked_dirs = [
        kase_home / "skills" / ".hub",
        kase_home / "mcp-tokens",
    ]
    for bd in blocked_dirs:
        try:
            resolved.relative_to(bd)
            return f"Access denied: {path} is an internal Kase file."
        except ValueError:
            continue
    
    credential_files = {"auth.json", ".env", ".anthropic_oauth.json"}
    for cf in credential_files:
        if resolved == (kase_home / cf).resolve():
            return f"Access denied: {path} is a Kase credential store."
    
    return None
