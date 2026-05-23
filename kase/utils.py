import json
import os
from pathlib import Path
from typing import Any


def safe_json_loads(text: str) -> Any:
    if not text or not isinstance(text, str):
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def base_url_host_matches(url1: str, url2: str) -> bool:
    from urllib.parse import urlparse
    try:
        return (urlparse(url1).hostname or "") == (urlparse(url2).hostname or "")
    except Exception:
        return False


def is_truthy_value(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(val)


def get_kase_home() -> Path:
    override = os.getenv("KASE_HOME")
    return Path(override) if override else Path.home() / ".kase"


KASE_HOME = get_kase_home()
