"""Tool call loop detection and guardrails."""

import hashlib
import json
import threading
from typing import Any, Dict, List, Optional, Set


class ToolCallGuardrailConfig:
    def __init__(
        self,
        max_consecutive_failures: int = 3,
        max_identical_calls: int = 3,
        enabled: bool = True,
    ):
        self.max_consecutive_failures = max_consecutive_failures
        self.max_identical_calls = max_identical_calls
        self.enabled = enabled


class ToolGuardrailDecision:
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"


class ToolCallGuardrailController:
    def __init__(self, config: Optional[ToolCallGuardrailConfig] = None):
        self._config = config or ToolCallGuardrailConfig()
        self._call_history: Dict[str, List[str]] = {}
        self._failure_count: int = 0
        self._lock = threading.Lock()

    def _args_hash(self, name: str, args: Dict) -> str:
        raw = f"{name}:{json.dumps(args, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def check_tool_call(self, name: str, args: Dict) -> str:
        if not self._config.enabled:
            return ToolGuardrailDecision.ALLOW

        args_hash = self._args_hash(name, args)

        with self._lock:
            history = self._call_history.setdefault(name, [])
            history.append(args_hash)

            recent = history[-self._config.max_identical_calls:]
            if len(recent) >= self._config.max_identical_calls and len(set(recent)) == 1:
                return ToolGuardrailDecision.WARN

            return ToolGuardrailDecision.ALLOW

    def record_failure(self, name: str) -> None:
        with self._lock:
            self._failure_count += 1

    def check_failure_threshold(self) -> bool:
        with self._lock:
            return self._failure_count >= self._config.max_consecutive_failures

    def reset(self) -> None:
        with self._lock:
            self._call_history.clear()
            self._failure_count = 0
