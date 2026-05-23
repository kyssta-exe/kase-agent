"""Toolset definitions for Kase Agent."""

from typing import Dict, List, Set

_KASE_CORE_TOOLS = [
    "web_search", "web_extract",
    "terminal", "process",
    "read_file", "write_file", "patch", "search_files",
    "vision_analyze", "image_generate",
    "skills_list", "skill_view", "skill_manage",
    "browser_navigate", "browser_snapshot", "browser_click",
    "browser_type", "browser_scroll", "browser_back",
    "browser_press", "browser_get_images",
    "browser_vision", "browser_console", "browser_cdp", "browser_dialog",
    "text_to_speech",
    "todo", "memory",
    "session_search",
    "clarify",
    "execute_code", "delegate_task",
    "cronjob",
    "send_message",
    "kanban_show", "kanban_list", "kanban_complete", "kanban_block",
    "kanban_heartbeat", "kanban_comment", "kanban_create", "kanban_link",
]

TOOLSETS: Dict[str, dict] = {
    "web": {
        "description": "Web research and content extraction",
        "tools": ["web_search", "web_extract"],
        "includes": []
    },
    "terminal": {
        "description": "Terminal and process management",
        "tools": ["terminal", "process"],
        "includes": []
    },
    "file": {
        "description": "File manipulation: read, write, patch, search",
        "tools": ["read_file", "write_file", "patch", "search_files"],
        "includes": []
    },
    "vision": {
        "description": "Image analysis and vision",
        "tools": ["vision_analyze"],
        "includes": []
    },
    "browser": {
        "description": "Browser automation",
        "tools": ["browser_navigate", "browser_snapshot", "browser_click",
                  "browser_type", "browser_scroll", "browser_back",
                  "browser_press", "browser_get_images", "browser_vision",
                  "browser_console", "browser_cdp", "browser_dialog", "web_search"],
        "includes": []
    },
    "memory": {
        "description": "Persistent memory and user profile",
        "tools": ["memory"],
        "includes": []
    },
    "delegation": {
        "description": "Subagent spawning for parallel work",
        "tools": ["delegate_task"],
        "includes": []
    },
    "code_execution": {
        "description": "Sandboxed code execution",
        "tools": ["execute_code"],
        "includes": []
    },
    "skills": {
        "description": "Skill management",
        "tools": ["skills_list", "skill_view", "skill_manage"],
        "includes": []
    },
    "cronjob": {
        "description": "Scheduled job management",
        "tools": ["cronjob"],
        "includes": []
    },
    "kanban": {
        "description": "Multi-agent kanban board",
        "tools": ["kanban_show", "kanban_list", "kanban_complete",
                  "kanban_block", "kanban_heartbeat", "kanban_comment",
                  "kanban_create", "kanban_link", "kanban_unblock"],
        "includes": []
    },
    "todo": {
        "description": "Task tracking and planning",
        "tools": ["todo"],
        "includes": []
    },
    "messaging": {
        "description": "Cross-platform messaging",
        "tools": ["send_message"],
        "includes": []
    },
    "search": {
        "description": "Web search only",
        "tools": ["web_search"],
        "includes": []
    },
    "image_gen": {
        "description": "Image generation",
        "tools": ["image_generate"],
        "includes": []
    },
    "kase-cli": {
        "description": "Default CLI toolset",
        "tools": _KASE_CORE_TOOLS.copy(),
        "includes": []
    },
    "kase-messaging": {
        "description": "Default messaging platform toolset",
        "tools": _KASE_CORE_TOOLS.copy(),
        "includes": []
    },
}


def get_toolset(toolset_name: str) -> List[str]:
    ts = TOOLSETS.get(toolset_name)
    if not ts:
        return []
    result = list(ts["tools"])
    for incl in ts.get("includes", []):
        result.extend(get_toolset(incl))
    return result


def resolve_toolset(names: List[str]) -> Set[str]:
    resolved: Set[str] = set()
    for name in names:
        tools = get_toolset(name)
        if tools:
            resolved.update(tools)
        else:
            resolved.add(name)
    return resolved


def get_all_toolsets() -> Dict[str, str]:
    return {k: v["description"] for k, v in TOOLSETS.items()}
