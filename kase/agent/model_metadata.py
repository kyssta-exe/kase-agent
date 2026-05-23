"""Model metadata, context length mapping, and token estimation."""

import json
import logging
import os
import re
from typing import Dict, Optional

logger = logging.getLogger(__name__)

MINIMUM_CONTEXT_LENGTH = 8192

DEFAULT_CONTEXT_LENGTHS = {
    "gpt-4": 8192, "gpt-4-32k": 32768, "gpt-4-turbo": 128000,
    "gpt-4o": 128000, "gpt-4o-mini": 128000, "o1": 200000, "o3": 200000,
    "claude-3": 200000, "claude-3-5": 200000, "claude-4": 200000,
    "gemini-1.5": 1048576, "gemini-2.0": 1048576, "gemini-2.5": 1048576,
    "gemma": 8192, "llama": 8192, "deepseek": 65536, "qwen": 32768,
    "mistral": 32768, "mixtral": 32768, "command-r": 128000,
    "sonar": 127000,
}

DEFAULT_CONTEXT_LENGTHS_LOWER = {k.lower(): v for k, v in DEFAULT_CONTEXT_LENGTHS.items()}


def get_model_context_length(model: str) -> int:
    if not model:
        return 128000
    model_lower = model.lower()
    sorted_keys = sorted(DEFAULT_CONTEXT_LENGTHS_LOWER.keys(), key=len, reverse=True)
    for key in sorted_keys:
        value = DEFAULT_CONTEXT_LENGTHS_LOWER[key]
        if key in model_lower or model_lower.startswith(key):
            return value
    return 128000


def estimate_messages_tokens_rough(messages: list) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += len(content) // 2
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    total += len(text) // 2
                    if block.get("type") == "image_url":
                        total += 1000
        role = msg.get("role", "")
        total += 4
    return total


def estimate_request_tokens_rough(messages: list, tools: list = None) -> int:
    msg_tokens = estimate_messages_tokens_rough(messages)
    tool_tokens = 0
    if tools:
        for tool in tools:
            schema = tool.get("function", tool)
            tool_tokens += len(json.dumps(schema)) // 2
    return msg_tokens + tool_tokens


def parse_available_output_tokens_from_error(error_str: str) -> Optional[int]:
    try:
        data = json.loads(error_str) if isinstance(error_str, str) else error_str
        msg = str(data.get("error", {}).get("message", str(data)))
    except (json.JSONDecodeError, AttributeError):
        msg = str(error_str)

    m = re.search(r"(\d+)\s*(?:more|available|remaining).*?tokens", msg, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"maximum.*?(\d+)", msg, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def parse_context_limit_from_error(error_str: str) -> Optional[int]:
    try:
        data = json.loads(error_str) if isinstance(error_str, str) else error_str
        msg = str(data.get("error", {}).get("message", str(data)))
    except (json.JSONDecodeError, AttributeError):
        msg = str(error_str)

    m = re.search(r"context.*?(\d+)", msg, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None


def save_context_length(model: str, context_length: int) -> None:
    _persistent_cache[model.lower()] = context_length


_persistent_cache: Dict[str, int] = {}
