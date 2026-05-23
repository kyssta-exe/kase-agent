"""Memory management - memory providers and orchestration."""

import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryProvider(ABC):
    @abstractmethod
    def initialize(self, config: dict) -> None:
        ...

    @abstractmethod
    def prefetch(self, query: str) -> Optional[str]:
        ...

    @abstractmethod
    def sync_turn(self, turn_messages: List[Dict[str, Any]]) -> None:
        ...

    def shutdown(self) -> None:
        ...


class KaseFileMemory(MemoryProvider):
    def __init__(self, kase_home: Optional[Path] = None):
        self._kase_home = kase_home or Path(os.getenv("KASE_HOME", Path.home() / ".kase"))
        self._memory_file = self._kase_home / "memory.json"
        self._user_file = self._kase_home / "user.md"
        self._in_memory: Dict[str, Any] = {}

    def initialize(self, config: dict) -> None:
        if self._memory_file.exists():
            try:
                self._in_memory = json.loads(self._memory_file.read_text(encoding="utf-8"))
            except Exception:
                self._in_memory = {}

    def prefetch(self, query: str) -> Optional[str]:
        if self._user_file.exists():
            return self._user_file.read_text(encoding="utf-8")[:4000]
        return None

    def sync_turn(self, turn_messages: List[Dict[str, Any]]) -> None:
        pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._in_memory.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._in_memory[key] = value
        self._save()

    def _save(self) -> None:
        self._memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._memory_file.write_text(json.dumps(self._in_memory, indent=2, ensure_ascii=False), encoding="utf-8")


class MemoryManager:
    def __init__(self, provider: Optional[MemoryProvider] = None):
        self._provider = provider or KaseFileMemory()

    def initialize(self, config: dict) -> None:
        self._provider.initialize(config)

    def prefetch(self, query: str) -> Optional[str]:
        return self._provider.prefetch(query)

    def sync_turn(self, turn_messages: List[Dict[str, Any]]) -> None:
        self._provider.sync_turn(turn_messages)

    def shutdown(self) -> None:
        self._provider.shutdown()


def build_memory_context_block(agent: Any) -> Optional[str]:
    if not agent.memory_manager:
        return None
    prefetch = agent.memory_manager.prefetch("")
    if prefetch:
        return f"[Memory Profile]\n{prefetch}\n[/Memory Profile]"
    return None


class StreamingContextScrubber:
    def process(self, chunk: str) -> str:
        return chunk
