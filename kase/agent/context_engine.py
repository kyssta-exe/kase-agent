"""Context engine ABC for pluggable context management."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ContextEngine(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    last_prompt_tokens: int = 0
    last_completion_tokens: int = 0
    last_total_tokens: int = 0
    threshold_tokens: int = 0
    context_length: int = 0
    compression_count: int = 0
    threshold_percent: float = 0.75
    protect_first_n: int = 3
    protect_last_n: int = 6

    @abstractmethod
    def update_from_response(self, usage: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def should_compress(self, prompt_tokens: int = None) -> bool:
        ...

    @abstractmethod
    def compress(self, messages: List[Dict[str, Any]], current_tokens: int = None, focus_topic: str = None) -> List[Dict[str, Any]]:
        ...

    def should_compress_preflight(self, messages: List[Dict[str, Any]]) -> bool:
        return False

    def has_content_to_compress(self, messages: List[Dict[str, Any]]) -> bool:
        return len(messages) > (self.protect_first_n + self.protect_last_n + 2)

    def on_session_start(self, session_id: str, **kwargs) -> None:
        ...

    def on_session_end(self, session_id: str, messages: List[Dict[str, Any]]) -> None:
        ...

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def handle_tool_call(self, name: str, args: Dict[str, Any], **kwargs) -> str:
        import json
        return json.dumps({"error": f"Unknown context engine tool: {name}"})

    def get_status(self) -> Dict[str, Any]:
        return {
            "last_prompt_tokens": self.last_prompt_tokens,
            "threshold_tokens": self.threshold_tokens,
            "context_length": self.context_length,
            "usage_percent": min(100, self.last_prompt_tokens / self.context_length * 100) if self.context_length else 0,
            "compression_count": self.compression_count,
        }
