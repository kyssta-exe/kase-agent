"""Message sanitization - surrogates, control chars, JSON repair."""

import json
import re
from typing import Any, Dict, List

_JSON_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def _sanitize_surrogates(text: str) -> str:
    return text.encode("utf-8", errors="surrogatepass").decode("utf-8", errors="replace")


def _sanitize_messages_surrogates(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for msg in messages:
        cleaned = {}
        for k, v in msg.items():
            if isinstance(v, str):
                cleaned[k] = _sanitize_surrogates(v)
            elif isinstance(v, list):
                cleaned[k] = [_sanitize_surrogates(item) if isinstance(item, str) else item for item in v]
            else:
                cleaned[k] = v
        result.append(cleaned)
    return result


def _sanitize_structure_surrogates(obj: Any) -> Any:
    if isinstance(obj, str):
        return _sanitize_surrogates(obj)
    if isinstance(obj, dict):
        return {k: _sanitize_structure_surrogates(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_structure_surrogates(item) for item in obj]
    return obj


def _strip_images_from_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    result = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, list):
            text = " ".join(
                c.get("text", "") for c in content
                if isinstance(c, dict) and c.get("type") == "text"
            )
            msg = msg.copy()
            msg["content"] = text.strip() or "[Images removed]"
        result.append(msg)
    return result


def _repair_tool_call_arguments(tool_calls: List[dict]) -> List[dict]:
    for tc in tool_calls:
        args = tc.get("function", {}).get("arguments", "")
        if isinstance(args, str):
            try:
                json.loads(args)
            except json.JSONDecodeError:
                fixed = _JSON_TRAILING_COMMA.sub(r"\1", args)
                try:
                    json.loads(fixed)
                    tc["function"]["arguments"] = fixed
                except json.JSONDecodeError:
                    pass
    return tool_calls
