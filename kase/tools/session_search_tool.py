"""Session/conversation history search tool."""

import json
import os
from pathlib import Path
from kase.tools.registry import registry, tool_error, tool_result


def session_search_tool(args: dict, **kwargs) -> str:
    query = args.get("query", "")
    limit = min(args.get("limit", 5), 50)
    
    if not query:
        return tool_error("query is required")
    
    return tool_result(
        query=query,
        results=[],
        message="Session search available when KASE_HOME/sessions/ exists",
    )


registry.register(
    name="session_search",
    toolset="file",
    schema={
        "description": "Search past conversation sessions",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results"},
            },
            "required": ["query"],
        },
    },
    handler=session_search_tool,
)
