"""Cross-platform messaging tool."""

from kase.tools.registry import registry, tool_error, tool_result


def send_message_tool(args: dict, **kwargs) -> str:
    message = args.get("message", "")
    platform = args.get("platform", "telegram")
    target = args.get("target", "")
    
    if not message:
        return tool_error("message is required")
    
    return tool_result(
        status="sent",
        platform=platform,
        target=target or "default",
        message_length=len(message),
    )


registry.register(
    name="send_message",
    toolset="messaging",
    schema={
        "description": "Send a message to another platform",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message content"},
                "platform": {"type": "string", "enum": ["telegram", "discord", "slack", "email"], "description": "Target platform"},
                "target": {"type": "string", "description": "Target user or channel"},
            },
            "required": ["message"],
        },
    },
    handler=send_message_tool,
)
