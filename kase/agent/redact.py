"""Secret redaction for logs and tool output."""

import os
import re

_REDACT_ENABLED = os.getenv("KASE_REDACT_SECRETS", "true").lower() in {"1", "true", "yes"}

_PREFIX_PATTERNS = [
    r"sk-[A-Za-z0-9_-]{10,}",
    r"ghp_[A-Za-z0-9]{10,}",
    r"github_pat_[A-Za-z0-9_]{10,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"AIza[A-Za-z0-9_-]{30,}",
    r"pplx-[A-Za-z0-9]{10,}",
    r"AKIA[A-Z0-9]{16}",
    r"hf_[A-Za-z0-9]{10,}",
]

_SENSITIVE_HEADERS = {
    "authorization", "x-api-key", "api-key", "cookie",
    "x-auth-token", "bearer", "set-cookie",
}


def _mask_token(m: re.Match) -> str:
    token = m.group(0)
    if len(token) < 18:
        return "*" * len(token)
    return token[:6] + "*" * (len(token) - 10) + token[-4:]


def redact_text(text: str) -> str:
    if not _REDACT_ENABLED or not text:
        return text
    for pattern in _PREFIX_PATTERNS:
        text = re.sub(pattern, _mask_token, text)
    return text


def redact_headers(headers: dict) -> dict:
    return {
        k: ("***REDACTED***" if k.lower() in _SENSITIVE_HEADERS else v)
        for k, v in headers.items()
    }
