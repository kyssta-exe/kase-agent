"""CLI presentation — spinner, previews, formatting."""

import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class LocalEditSnapshot:
    paths: list[Path] = field(default_factory=list)
    before: dict[str, Optional[str]] = field(default_factory=dict)


class KawaiiSpinner:
    _WAITING_FACES = ["(◕‿◕)", "(◡‿◡)", "(◕‿◕✿)", "(◠‿◠)", "(⌒‿⌒)"]
    _THINKING_FACES = ["(｡•᎔•｡)", "(｡•́︿•̀｡)", "(◕‸◕✿)", "(╥﹏╥)", "(✿◕‿◕)"]
    _THINKING_VERBS = ["thinking", "pondering", "calculating", "processing", "analyzing"]
    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._phase = "waiting"

    def start(self, text: str = "") -> None:
        if self.quiet or sys.stdout.isatty() is False:
            return
        self._running = True
        self._phase = "thinking"
        self._thread = threading.Thread(target=self._spin, args=(text,), daemon=True)
        self._thread.start()

    def _spin(self, text: str) -> None:
        idx = 0
        while self._running:
            face = self._THINKING_FACES[idx % len(self._THINKING_FACES)]
            verb = self._THINKING_VERBS[idx % len(self._THINKING_VERBS)]
            frame = self._FRAMES[idx % len(self._FRAMES)]
            msg = f"\r{frame} {face} {verb}... {text}" if text else f"\r{frame} {face} {verb}..."
            sys.stdout.write(msg)
            sys.stdout.flush()
            time.sleep(0.12)
            idx += 1

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()

    def succeed(self, text: str = "") -> None:
        self.stop()
        if text:
            sys.stdout.write(f"\r✓ {text}\n")
            sys.stdout.flush()

    def fail(self, text: str = "") -> None:
        self.stop()
        if text:
            sys.stdout.write(f"\r✗ {text}\n")
            sys.stdout.flush()


def build_tool_preview(tool_name: str, args: dict, max_len: Optional[int] = None) -> Optional[str]:
    if not args:
        return None
    
    primary_keys = {
        "terminal": "command", "web_search": "query", "read_file": "path",
        "write_file": "path", "search_files": "pattern", "web_extract": "url",
        "browser_navigate": "url", "execute_code": "code", "delegate_task": "goal",
    }
    
    key = primary_keys.get(tool_name)
    if not key:
        return f" {tool_name}"
    
    val = args.get(key, "")
    text = str(val)[:120]
    if len(str(val)) > 120:
        text += "..."
    
    text = " ".join(text.split())
    if max_len and len(text) > max_len:
        text = text[:max_len] + "..."
    
    return f" {tool_name} ({text})"


TOOL_EMOJIS = {
    "terminal": "⎇", "web_search": "◎", "read_file": "≡", "write_file": "✎",
    "search_files": "⌕", "web_extract": "⇣", "browser_navigate": "➜",
    "execute_code": "▶", "delegate_task": "⚑", "memory": "♡",
    "vision_analyze": "◉", "todo": "☐",
}
