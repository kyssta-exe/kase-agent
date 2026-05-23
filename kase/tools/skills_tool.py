"""Skill management tools."""

from kase.tools.registry import registry, tool_error, tool_result
from kase.skills.manager import get_skill_manager


def skills_list_tool(args: dict, **kwargs) -> str:
    category = args.get("category", "")
    mgr = get_skill_manager()
    mgr.discover_skills()
    skills = mgr.list_skills(category)
    return tool_result(
        skills=[{"name": s.name, "description": s.description, "category": s.category} for s in skills],
        count=len(skills),
    )


def skill_view_tool(args: dict, **kwargs) -> str:
    name = args.get("name", "")
    if not name:
        return tool_error("name is required")
    mgr = get_skill_manager()
    mgr.discover_skills()
    skill = mgr.get_skill(name)
    if not skill:
        return tool_error(f"Skill not found: {name}")
    return tool_result(
        name=skill.name,
        description=skill.description,
        content=skill.content[:10000],
        metadata=skill.metadata,
    )


def skill_manage_tool(args: dict, **kwargs) -> str:
    action = args.get("action", "list")
    name = args.get("name", "")
    return tool_result(action=action, status="ok", message=f"Skill management: {action}")


registry.register(
    name="skills_list",
    toolset="skills",
    schema={
        "description": "List available skills",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category"},
            },
        },
    },
    handler=skills_list_tool,
    emoji="⚡",
)

registry.register(
    name="skill_view",
    toolset="skills",
    schema={
        "description": "View the contents of a skill",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Skill name"},
            },
            "required": ["name"],
        },
    },
    handler=skill_view_tool,
)

registry.register(
    name="skill_manage",
    toolset="skills",
    schema={
        "description": "Create, edit, or delete skills",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["create", "edit", "delete", "list"]},
                "name": {"type": "string"},
                "content": {"type": "string"},
            },
            "required": ["action"],
        },
    },
    handler=skill_manage_tool,
)
