"""Clarifying questions tool."""

from kase.tools.registry import registry, tool_result


def clarify_tool(args: dict, **kwargs) -> str:
    question = args.get("question", "")
    return tool_result(question=question, status="asked")


registry.register(
    name="clarify",
    toolset="file",
    schema={
        "description": "Ask the user a clarifying question when requirements are ambiguous",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question to ask"},
            },
            "required": ["question"],
        },
    },
    handler=clarify_tool,
)
