"""Context compression using summarization."""

from typing import Any, Dict, List, Optional
from kase.agent.context_engine import ContextEngine


class ContextCompressor(ContextEngine):
    def __init__(self, context_length: int = 128000, threshold_percent: float = 0.75):
        self._context_length = context_length
        self.threshold_percent = threshold_percent
        self.compression_count = 0
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.threshold_tokens = int(context_length * threshold_percent)

    @property
    def name(self) -> str:
        return "compressor"

    @property
    def context_length(self) -> int:
        return self._context_length

    @context_length.setter
    def context_length(self, value: int) -> None:
        self._context_length = value
        self.threshold_tokens = int(value * self.threshold_percent)

    def update_from_response(self, usage: Dict[str, Any]) -> None:
        self.last_prompt_tokens = usage.get("prompt_tokens", 0)
        self.last_completion_tokens = usage.get("completion_tokens", 0)
        self.last_total_tokens = usage.get("total_tokens", 0)

    def should_compress(self, prompt_tokens: int = None) -> bool:
        tokens = prompt_tokens or self.last_prompt_tokens
        return tokens > self.threshold_tokens

    def compress(self, messages: List[Dict[str, Any]], current_tokens: int = None, focus_topic: str = None) -> List[Dict[str, Any]]:
        if len(messages) <= self.protect_first_n + self.protect_last_n + 1:
            return messages
        
        protected = messages[:self.protect_first_n]
        tail = messages[-self.protect_last_n:] if self.protect_last_n else []
        compressible = messages[self.protect_first_n:-self.protect_last_n] if self.protect_last_n else messages[self.protect_first_n:]
        
        summary = self._summarize(compressible, focus_topic)
        
        result = protected + [{"role": "system", "content": f"[Compressed context: {summary}]"}] + tail
        self.compression_count += 1
        return result

    def _summarize(self, messages: List[Dict[str, Any]], focus: Optional[str] = None) -> str:
        tool_calls = sum(1 for m in messages if m.get("role") == "assistant" and m.get("tool_calls"))
        user_msgs = sum(1 for m in messages if m.get("role") == "user")
        tool_results = sum(1 for m in messages if m.get("role") == "tool")
        return f"{user_msgs} user messages, {tool_calls} tool calls, {tool_results} tool results. Focus: {focus or 'general'}"

    def on_session_reset(self) -> None:
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.compression_count = 0
