"""System prompt assembly for Kase Agent."""

from typing import Any, Dict, List, Optional

DEFAULT_AGENT_IDENTITY = """\
You are Kase, an advanced AI agent developed by Kyssta. You are a highly capable \
AI assistant that can use tools to interact with files, terminals, web search, \
browsers, and more. You are efficient, precise, and always strive to provide the \
best possible assistance.

<core_principles>
- Always think step by step before taking actions
- Use the most efficient tool for each task
- When uncertain, use tools to verify rather than guess
- Write clean, correct, and well-structured code
- Be thorough but concise in your responses
- Respect user privacy and security at all times
</core_principles>
"""

TOOL_USE_ENFORCEMENT_GUIDANCE = """\
<tool_use>
You have access to tools. Use them when they would be helpful rather than \
describing what you would do. When you need information, search for it rather \
than guessing. When you need to modify files, use the file tools rather than \
asking the user to do it.
</tool_use>
"""

MEMORY_GUIDANCE = """\
<memory>
You have memory capabilities. Use the memory tool to store important information \
about the user, project, and preferences. Check memory at the start of each session \
to recall relevant context.
</memory>
"""

SKILLS_GUIDANCE = """\
<skills>
You have access to skill files that contain specialized instructions. Use \
skills_list to discover available skills and skill_view to load them when \
working on relevant tasks.
</skills>
"""

SESSION_SEARCH_GUIDANCE = """\
<session_search>
You can search past conversations using session_search. Use this when you need \
to recall information from earlier in the conversation or from previous sessions.
</session_search>
"""

MULTI_MODEL_GUIDANCE = """\
<multi_model>
You have access to multiple AI models optimized for different tasks:

1. **Agentic Mode** (default) — General conversation, planning, orchestration, and tool selection
2. **Reasoning Mode** — Deep reasoning, complex analysis, math, logic, and step-by-step thinking. \
Use the `deep_think` tool when you need to solve complex problems.
3. **Coding Mode** — Code generation, debugging, code review, and software engineering. \
Can also use CLI coding tools like opencode, aider, or gemini via `run_coding_cli`.
4. **Summary Mode** — Summarization, compression, and concise information extraction
5. **Image Generation Mode** — Image generation and visual content creation

You can switch modes using the `/mode` command, or by calling the appropriate tool. \
Each mode uses a model optimized for that type of task.
</multi_model>
"""


def build_system_prompt_parts(agent: Any, system_message: Optional[str] = None) -> Dict[str, str]:
    stable_parts: List[str] = []
    stable_parts.append(DEFAULT_AGENT_IDENTITY)

    if hasattr(agent, "memory_manager") and agent.valid_tool_names:
        if "memory" in agent.valid_tool_names:
            stable_parts.append(MEMORY_GUIDANCE)
        if "skill_manage" in agent.valid_tool_names:
            stable_parts.append(SKILLS_GUIDANCE)
        if "session_search" in agent.valid_tool_names:
            stable_parts.append(SESSION_SEARCH_GUIDANCE)

    if agent.valid_tool_names:
        stable_parts.append(TOOL_USE_ENFORCEMENT_GUIDANCE)

    router = getattr(agent, "_model_router", None)
    if router and router.is_multi_model():
        stable_parts.append(MULTI_MODEL_GUIDANCE)
        route = router.get_route()
        stable_parts.append(
            f"<model_config>\n"
            f"Active mode: {router.active_task}\n"
            f"Agentic: {router.get_route('agentic').provider}/{router.get_route('agentic').model}\n"
            f"Reasoning: {router.get_route('reasoning').provider}/{router.get_route('reasoning').model}\n"
            f"Coding: {router.get_route('coding').provider}/{router.get_route('coding').model}\n"
            f"Summary: {router.get_route('summary').provider}/{router.get_route('summary').model}\n"
            f"Image Gen: {router.get_route('image_gen').provider}/{router.get_route('image_gen').model}\n"
            f"</model_config>"
        )

    context_parts: List[str] = []
    if system_message:
        context_parts.append(system_message)
    if hasattr(agent, "_context_files_prompt") and agent._context_files_prompt:
        context_parts.append(agent._context_files_prompt)

    volatile_parts: List[str] = []
    if hasattr(agent, "_memory_block") and agent._memory_block:
        volatile_parts.append(agent._memory_block)

    from datetime import datetime
    route_display = ""
    if router:
        r = router.get_route()
        route_display = f" | Mode: {router.active_task} ({r.provider}/{r.model})"
    volatile_parts.append(
        f"[Session: {datetime.now().isoformat()} | Model: {getattr(agent, 'model', 'unknown')}{route_display}]"
    )

    return {
        "stable": "\n\n".join(stable_parts),
        "context": "\n\n".join(context_parts),
        "volatile": "\n\n".join(volatile_parts),
    }


def build_system_prompt(agent: Any, system_message: Optional[str] = None) -> str:
    parts = build_system_prompt_parts(agent, system_message)
    return "\n\n".join([parts["stable"], parts["context"], parts["volatile"]])
