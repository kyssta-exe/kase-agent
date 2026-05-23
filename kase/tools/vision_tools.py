"""Image analysis and vision tools."""

import json
from kase.tools.registry import registry, tool_error, tool_result


def vision_analyze_tool(args: dict, **kwargs) -> str:
    question = args.get("question", "")
    images = args.get("images", [])
    
    if not images:
        return tool_error("at least one image is required")
    
    return tool_result(
        analysis=f"[Vision analysis would process {len(images)} image(s)]",
        question=question,
        image_count=len(images),
    )


registry.register(
    name="vision_analyze",
    toolset="vision",
    schema={
        "description": "Analyze images using vision-capable models",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question about the image(s)"},
                "images": {
                    "type": "array",
                    "items": {"type": "string", "description": "Image URL or base64 data"},
                    "description": "Images to analyze",
                },
            },
            "required": ["images"],
        },
    },
    handler=vision_analyze_tool,
    emoji="◉",
)
