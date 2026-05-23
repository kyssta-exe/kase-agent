"""Image generation tools."""

from kase.tools.registry import registry, tool_error, tool_result


def image_generate_tool(args: dict, **kwargs) -> str:
    prompt = args.get("prompt", "")
    if not prompt:
        return tool_error("prompt is required")
    return tool_result(
        status="generated",
        prompt=prompt,
        url="[Image generation requires an image provider like OpenAI DALL-E or Fal.ai]",
    )


registry.register(
    name="image_generate",
    toolset="image_gen",
    schema={
        "description": "Generate images from text descriptions",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Image description"},
                "size": {"type": "string", "enum": ["1024x1024", "1792x1024", "1024x1792"]},
            },
            "required": ["prompt"],
        },
    },
    handler=image_generate_tool,
    emoji="🎨",
)
