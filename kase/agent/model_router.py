"""Model router — per-task model selection for multi-model mode."""

import json
import logging
import os
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


TASK_AGENTIC = "agentic"
TASK_REASONING = "reasoning"
TASK_SUMMARY = "summary"
TASK_CODING = "coding"
TASK_IMAGE_GEN = "image_gen"

ALL_TASK_TYPES = [TASK_AGENTIC, TASK_REASONING, TASK_SUMMARY, TASK_CODING, TASK_IMAGE_GEN]

TOOL_TO_TASK = {
    "execute_code": TASK_CODING,
    "image_generate": TASK_IMAGE_GEN,
    "vision_analyze": TASK_REASONING,
    "web_search": TASK_AGENTIC,
    "web_extract": TASK_AGENTIC,
    "terminal": TASK_CODING,
    "browser_navigate": TASK_AGENTIC,
}

TASK_DESCRIPTIONS = {
    TASK_AGENTIC: "General conversation, planning, orchestration, and tool selection",
    TASK_REASONING: "Deep reasoning, complex analysis, math, logic, and step-by-step thinking",
    TASK_SUMMARY: "Summarization, compression, and concise information extraction",
    TASK_CODING: "Code generation, debugging, code review, and software engineering",
    TASK_IMAGE_GEN: "Image generation and visual content creation",
}


@dataclass
class CodingCLITool:
    name: str
    command: str
    args_template: str = "{task}"
    description: str = ""
    working_dir: str = ""
    timeout: int = 300

    def build_command(self, task: str, cwd: str = "") -> List[str]:
        import shlex
        args = self.args_template.format(task=task)
        return [self.command] + shlex.split(args)


@dataclass
class ModelRoute:
    task_type: str
    model: str
    provider: str = "openai"
    base_url: str = ""
    api_key: str = ""
    context_length: int = 128000
    temperature: float = 0.7
    description: str = ""
    fallbacks: List["ModelRoute"] = field(default_factory=list)
    cli_tools: List[CodingCLITool] = field(default_factory=list)

    def __post_init__(self):
        if not self.description:
            self.description = TASK_DESCRIPTIONS.get(self.task_type, "")
        if isinstance(self.fallbacks, list):
            self.fallbacks = [
                fb if isinstance(fb, ModelRoute) else ModelRoute(**fb)
                for fb in self.fallbacks
            ]


_DEFAULT_FALLBACKS = {
    TASK_AGENTIC: [
        ModelRoute(task_type=TASK_AGENTIC, model="gpt-4o-mini", provider="openai",
                   description="Fallback: faster/cheaper agentic model"),
    ],
    TASK_REASONING: [
        ModelRoute(task_type=TASK_REASONING, model="gpt-4o", provider="openai",
                   description="Fallback: general model for reasoning"),
        ModelRoute(task_type=TASK_REASONING, model="gpt-4o-mini", provider="openai",
                   description="Fallback: lightweight reasoning"),
    ],
    TASK_SUMMARY: [
        ModelRoute(task_type=TASK_SUMMARY, model="gpt-4o-mini", provider="openai",
                   description="Fallback: cheaper summarization"),
    ],
    TASK_CODING: [
        ModelRoute(task_type=TASK_CODING, model="gpt-4o", provider="openai",
                   description="Fallback: general coding model"),
        ModelRoute(task_type=TASK_CODING, model="gpt-4o-mini", provider="openai",
                   description="Fallback: lightweight coding"),
    ],
    TASK_IMAGE_GEN: [
        ModelRoute(task_type=TASK_IMAGE_GEN, model="dall-e-3", provider="openai",
                   description="Fallback: default image gen"),
    ],
}

_DEFAULT_CLI_CODING_TOOLS = [
    CodingCLITool(
        name="opencode",
        command="opencode",
        args_template="{task}",
        description="OpenCode CLI agent for coding tasks",
        timeout=600,
    ),
    CodingCLITool(
        name="gemini",
        command="gemini",
        args_template="--task {task}",
        description="Gemini CLI for coding and analysis",
        timeout=600,
    ),
    CodingCLITool(
        name="claude",
        command="claude",
        args_template='{task}',
        description="Claude Code CLI for software engineering",
        timeout=600,
    ),
    CodingCLITool(
        name="aider",
        command="aider",
        args_template="--message {task}",
        description="Aider AI pair programming CLI",
        timeout=600,
    ),
]


_DEFAULT_ROUTES = {
    TASK_AGENTIC: ModelRoute(
        task_type=TASK_AGENTIC, model="gpt-4o", provider="openai",
        base_url="https://api.openai.com/v1", context_length=128000,
        fallbacks=_DEFAULT_FALLBACKS[TASK_AGENTIC],
    ),
    TASK_REASONING: ModelRoute(
        task_type=TASK_REASONING, model="o1", provider="openai",
        base_url="https://api.openai.com/v1", context_length=200000,
        temperature=1.0,
        fallbacks=_DEFAULT_FALLBACKS[TASK_REASONING],
    ),
    TASK_SUMMARY: ModelRoute(
        task_type=TASK_SUMMARY, model="gpt-4o-mini", provider="openai",
        base_url="https://api.openai.com/v1", context_length=128000,
        temperature=0.3,
        fallbacks=_DEFAULT_FALLBACKS[TASK_SUMMARY],
    ),
    TASK_CODING: ModelRoute(
        task_type=TASK_CODING, model="gpt-4o", provider="openai",
        base_url="https://api.openai.com/v1", context_length=128000,
        fallbacks=_DEFAULT_FALLBACKS[TASK_CODING],
        cli_tools=_DEFAULT_CLI_CODING_TOOLS,
    ),
    TASK_IMAGE_GEN: ModelRoute(
        task_type=TASK_IMAGE_GEN, model="dall-e-3", provider="openai",
        base_url="https://api.openai.com/v1", context_length=128000,
        fallbacks=_DEFAULT_FALLBACKS[TASK_IMAGE_GEN],
    ),
}


def _resolve_api_key(route: ModelRoute) -> str:
    if route.api_key:
        return route.api_key
    provider_upper = route.provider.upper()
    key = os.getenv(f"{provider_upper}_API_KEY", "")
    if key:
        return key
    if route.provider == "openai":
        return os.getenv("OPENAI_API_KEY", "")
    if route.provider == "anthropic":
        return os.getenv("ANTHROPIC_API_KEY", "")
    if route.provider == "gemini":
        return os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    return os.getenv("OPENAI_API_KEY", "")


def _resolve_base_url(route: ModelRoute) -> str:
    if route.base_url:
        return route.base_url
    provider_upper = route.provider.upper()
    env_url = os.getenv(f"{provider_upper}_BASE_URL", "")
    if env_url:
        return env_url
    return f"https://api.{route.provider}.com/v1" if route.provider not in ("openai", "azure", "vertex") else ""


def _create_client(route: ModelRoute):
    import openai
    api_key = _resolve_api_key(route)
    base_url = _resolve_base_url(route)
    return openai.OpenAI(api_key=api_key or "", base_url=base_url or None)


def _run_cli_tool(tool: CodingCLITool, task: str, cwd: str = "") -> str:
    full_cmd = tool.build_command(task, cwd)
    workdir = cwd or tool.working_dir or os.getcwd()
    try:
        result = subprocess.run(
            full_cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            timeout=tool.timeout,
            shell=(sys.platform == "win32"),
        )
        output = result.stdout[-50000:] if result.stdout else ""
        if result.stderr:
            output += f"\n--- stderr ---\n{result.stderr[-10000:]}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"(CLI tool {tool.name} timed out after {tool.timeout}s)"
    except FileNotFoundError:
        return f"(CLI tool {tool.name} not found — install it or check PATH)"
    except Exception as e:
        return f"(CLI tool {tool.name} error: {e})"


class ModelRouter:
    def __init__(self, routes: Optional[Dict[str, ModelRoute]] = None):
        self._routes: Dict[str, ModelRoute] = {}
        self._clients: Dict[str, Any] = {}
        self._active_task: str = TASK_AGENTIC

        if routes:
            for task, route in routes.items():
                if task in ALL_TASK_TYPES:
                    self._routes[task] = route
        for task in ALL_TASK_TYPES:
            if task not in self._routes:
                self._routes[task] = _DEFAULT_ROUTES[task]

    @property
    def active_task(self) -> str:
        return self._active_task

    @active_task.setter
    def active_task(self, value: str) -> None:
        if value in ALL_TASK_TYPES:
            self._active_task = value

    def get_route(self, task_type: Optional[str] = None) -> ModelRoute:
        task = task_type or self._active_task
        return self._routes.get(task, self._routes[TASK_AGENTIC])

    def detect_task_type(self, tool_name: str = "",
                         messages: Optional[List[Dict]] = None) -> str:
        if tool_name in TOOL_TO_TASK:
            return TOOL_TO_TASK[tool_name]

        if messages:
            last_content = ""
            for m in reversed(messages):
                content = m.get("content", "")
                if isinstance(content, str) and content:
                    last_content = content
                    break
            if last_content:
                reasoning_keywords = [
                    "think step by step", "deep reasoning", "solve", "calculate",
                    "explain complex", "analyze deeply", "reason about", "why does",
                    "proof", "deduce", "infer",
                ]
                if any(kw in last_content.lower() for kw in reasoning_keywords):
                    return TASK_REASONING

                coding_keywords = [
                    "write code", "implement", "debug", "refactor", "create function",
                    "fix bug", "add feature", "pull request", "commit",
                ]
                if any(kw in last_content.lower() for kw in coding_keywords):
                    return TASK_CODING

        return TASK_AGENTIC

    def get_client(self, task_type: Optional[str] = None,
                   fallback_attempt: int = 0) -> Any:
        route = self._get_effective_route(task_type, fallback_attempt)
        cache_key = f"{route.provider}:{route.base_url}"
        if cache_key not in self._clients:
            self._clients[cache_key] = _create_client(route)
        return self._clients[cache_key]

    def _get_effective_route(self, task_type: Optional[str] = None,
                             fallback_attempt: int = 0) -> ModelRoute:
        route = self.get_route(task_type)
        if fallback_attempt > 0 and route.fallbacks:
            idx = min(fallback_attempt - 1, len(route.fallbacks) - 1)
            return route.fallbacks[idx]
        return route

    def route_for_tool(self, tool_name: str) -> ModelRoute:
        task = self.detect_task_type(tool_name=tool_name)
        return self.get_route(task)

    def call_llm(self, messages: List[Dict], task_type: Optional[str] = None,
                 tools: Optional[List[Dict]] = None, max_tokens: int = None,
                 **kwargs) -> Optional[Dict]:
        route = self.get_route(task_type)
        last_error = None

        attempts = [route] + (route.fallbacks or [])
        for attempt_idx, attempt_route in enumerate(attempts):
            try:
                client = _create_client(attempt_route)
                call_kwargs = {
                    "model": attempt_route.model,
                    "messages": messages,
                    "stream": False,
                }
                if max_tokens:
                    call_kwargs["max_tokens"] = max_tokens
                if (attempt_route.temperature is not None
                        and "o1" not in attempt_route.model
                        and "o3" not in attempt_route.model):
                    call_kwargs["temperature"] = attempt_route.temperature
                if tools:
                    call_kwargs["tools"] = tools

                response = client.chat.completions.create(**call_kwargs)

                choice = response.choices[0] if response.choices else None
                if not choice:
                    continue

                message = choice.message
                result = {
                    "content": message.content or "",
                    "role": "assistant",
                    "model": attempt_route.model,
                    "provider": attempt_route.provider,
                    "task_type": task_type or self._active_task,
                    "fallback_used": attempt_idx > 0,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    },
                }

                if message.tool_calls:
                    result["tool_calls"] = [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ]

                if attempt_idx > 0:
                    logger.info("LLM call fell back to %s/%s after %d failures",
                                attempt_route.provider, attempt_route.model, attempt_idx)

                return result

            except Exception as e:
                last_error = e
                logger.warning("LLM call failed (attempt %d, model=%s/%s): %s",
                               attempt_idx + 1, attempt_route.provider,
                               attempt_route.model, e)
                continue

        logger.error("All %d LLM attempts failed for task=%s. Last error: %s",
                     len(attempts), task_type or self._active_task, last_error)
        return None

    def call_coding_cli(self, task: str, cwd: str = "") -> Dict:
        route = self.get_route(TASK_CODING)
        if not route.cli_tools:
            return {"success": False, "error": "No CLI coding tools configured"}

        results = []
        for tool in route.cli_tools:
            try:
                available = subprocess.run(
                    [tool.command, "--version"],
                    capture_output=True, text=True, timeout=10,
                    shell=(sys.platform == "win32"),
                )
            except (FileNotFoundError, subprocess.TimeoutExpired):
                results.append({"tool": tool.name, "available": False})
                continue

            results.append({"tool": tool.name, "available": True})
            output = _run_cli_tool(tool, task, cwd)
            return {
                "success": True,
                "tool": tool.name,
                "output": output,
                "results": results,
            }

        return {
            "success": False,
            "error": "No available CLI coding tools found",
            "results": results,
        }

    def get_available_cli_tools(self) -> List[Dict]:
        available = []
        for tool in _DEFAULT_CLI_CODING_TOOLS:
            try:
                subprocess.run(
                    [tool.command, "--version"],
                    capture_output=True, text=True, timeout=10,
                    shell=(sys.platform == "win32"),
                )
                available.append({"name": tool.name, "command": tool.command,
                                  "description": tool.description, "available": True})
            except (FileNotFoundError, subprocess.TimeoutExpired):
                available.append({"name": tool.name, "command": tool.command,
                                  "description": tool.description, "available": False})
        return available

    def summarize(self, text: str, max_tokens: int = 500) -> Optional[str]:
        route = self.get_route(TASK_SUMMARY)
        try:
            client = _create_client(route)
            response = client.chat.completions.create(
                model=route.model,
                messages=[
                    {"role": "system",
                     "content": "Summarize the following content concisely. "
                                "Capture key facts, decisions, and code changes."},
                    {"role": "user", "content": text[:15000]},
                ],
                max_tokens=max_tokens,
                temperature=route.temperature,
            )
            return response.choices[0].message.content
        except Exception as e:
            if route.fallbacks:
                for fb in route.fallbacks:
                    try:
                        fb_client = _create_client(fb)
                        resp = fb_client.chat.completions.create(
                            model=fb.model,
                            messages=[
                                {"role": "system",
                                 "content": "Summarize concisely."},
                                {"role": "user", "content": text[:15000]},
                            ],
                            max_tokens=max_tokens,
                        )
                        return resp.choices[0].message.content
                    except Exception:
                        continue
            logger.warning("ModelRouter summarization failed: %s", e)
            return None

    def set_route(self, task_type: str, route: ModelRoute) -> None:
        if task_type in ALL_TASK_TYPES:
            self._routes[task_type] = route
            cache_key = f"{route.provider}:{route.base_url}"
            self._clients.pop(cache_key, None)

    def get_all_routes(self) -> Dict[str, ModelRoute]:
        return dict(self._routes)

    def is_multi_model(self) -> bool:
        models = {r.model for r in self._routes.values()}
        return len(models) > 1

    def config_to_dict(self) -> Dict:
        return {
            task: {
                "model": route.model,
                "provider": route.provider,
                "base_url": route.base_url,
                "context_length": route.context_length,
                "temperature": route.temperature,
                "fallbacks": [
                    {"model": fb.model, "provider": fb.provider}
                    for fb in (route.fallbacks or [])
                ],
                "cli_tools": [
                    {"name": t.name, "command": t.command}
                    for t in (route.cli_tools or [])
                ],
            }
            for task, route in self._routes.items()
        }

    def get_status(self) -> Dict:
        cli_tools_status = self.get_available_cli_tools()
        return {
            "multi_model": self.is_multi_model(),
            "active_task": self._active_task,
            "routes": {
                task: {
                    "model": route.model,
                    "provider": route.provider,
                    "context_length": route.context_length,
                    "has_fallbacks": bool(route.fallbacks),
                    "cli_tools": [t.name for t in (route.cli_tools or [])],
                }
                for task, route in self._routes.items()
            },
            "cli_tools": cli_tools_status,
        }
