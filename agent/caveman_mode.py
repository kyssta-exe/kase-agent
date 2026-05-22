"""Caveman mode state management.

Token-efficient mode that reduces output verbosity.
Levels: off, lite, normal, max, ultra (default: off).
"""

import threading
from typing import Optional

_lock = threading.Lock()
_current_level: str = "off"  # off | lite | normal | max | ultra

LEVELS = ("off", "lite", "normal", "max", "ultra")

CAVEMAN_INSTRUCTIONS: dict[str, str] = {
    "off": "",
    "lite": (
        "You are in **lite caveman mode**. Be concise: drop filler words, "
        "hedging, pleasantries. Keep articles and full sentences. Professional "
        "but tight. No 'Sure! I'd be happy to help.' Just answer directly."
    ),
    "normal": (
        "You are in **caveman mode**. Speak like a smart technical caveman: "
        "drop articles (a/an/the), filler words (just/really/basically), "
        "pleasantries, hedging. Use fragments where clear. Short synonyms "
        "preferred. Code blocks unchanged. Errors quoted exact. "
        "Pattern: [thing] [action] [reason]. [next step]. "
        "Not: 'Sure! I'd be happy to help with that. The issue is...' "
        "Yes: 'Bug in auth middleware. Token expiry check uses < not <=. Fix:' "
        "Stay terse. No fluff."
    ),
    "max": (
        "You are in **max caveman mode**. Maximum conciseness. Drop all filler, "
        "articles, conjunctions where possible. Heavy use of fragments. "
        "Technical terms exact. Code/symbols never abbreviated. "
        "Pattern: [thing] [action] → [result]. "
        "Security warnings and multi-step destructive ops: full clarity."
    ),
    "ultra": (
        "You are in **ultra caveman mode**. Extreme abbreviation. Abbreviate "
        "common prose words (DB/auth/config/req/res/fn/impl). Strip conjunctions. "
        "Use arrows for causality (X → Y). One word when one word enough. "
        "Code symbols, function names, API names, error strings: never abbreviate. "
        "Security warnings and destructive ops: full clarity, then resume."
    ),
}


def set_level(level: str) -> str:
    """Set caveman mode level. Returns normalized level or error msg."""
    level = level.strip().lower()
    if level in LEVELS:
        with _lock:
            global _current_level
            _current_level = level
        return level
    return f"invalid level '{level}'. choose from: {', '.join(LEVELS)}"


def get_level() -> str:
    with _lock:
        return _current_level


def get_instruction() -> str:
    return CAVEMAN_INSTRUCTIONS.get(get_level(), "")


def is_active() -> bool:
    return get_level() != "off"


def toggle(level: Optional[str] = None) -> str:
    """Toggle or set. No arg: cycle off→normal→off. Arg: set specific."""
    if level:
        return set_level(level)
    current = get_level()
    if current == "off":
        return set_level("normal")
    return set_level("off")
