"""Base transport definitions."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NormalizedToolCall:
    id: str = ""
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class NormalizedResponse:
    content: str = ""
    tool_calls: List[NormalizedToolCall] = field(default_factory=list)
    usage: Optional[NormalizedUsage] = None
    reasoning: str = ""
    finish_reason: str = ""
