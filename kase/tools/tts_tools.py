"""Text-to-speech tools."""

from kase.tools.registry import registry, tool_error, tool_result


def text_to_speech_tool(args: dict, **kwargs) -> str:
    text = args.get("text", "")
    voice = args.get("voice", "alloy")
    if not text:
        return tool_error("text is required")
    return tool_result(
        status="generated",
        text_length=len(text),
        voice=voice,
        url="[TTS requires OpenAI TTS or Edge TTS configured]",
    )


registry.register(
    name="text_to_speech",
    toolset="tts",
    schema={
        "description": "Convert text to speech audio",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "voice": {"type": "string", "enum": ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]},
            },
            "required": ["text"],
        },
    },
    handler=text_to_speech_tool,
)
