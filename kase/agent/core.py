"""Kase AIAgent — the main agent orchestrator."""

import json
import logging
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from kase.agent.context_compressor import ContextCompressor
from kase.agent.context_engine import ContextEngine
from kase.agent.credential_pool import CredentialPool
from kase.agent.display import KawaiiSpinner
from kase.agent.error_classifier import FailoverReason, classify_api_error, should_fallback, should_retry
from kase.agent.iteration_budget import IterationBudget
from kase.agent.memory_manager import MemoryManager, build_memory_context_block
from kase.agent.message_sanitization import (
    _repair_tool_call_arguments,
    _sanitize_messages_surrogates,
    _strip_images_from_messages,
)
from kase.agent.model_metadata import (
    estimate_messages_tokens_rough,
    get_model_context_length,
    parse_available_output_tokens_from_error,
)
from kase.agent.long_term_memory import LongTermMemory
from kase.agent.model_router import ModelRouter, TASK_AGENTIC, TASK_REASONING, TASK_CODING, TASK_IMAGE_GEN, ALL_TASK_TYPES
from kase.web_panel.analytics import AnalyticsTracker
from kase.agent.system_prompt import build_system_prompt
from kase.agent.think_scrubber import StreamingThinkScrubber, strip_think_blocks
from kase.agent.tool_dispatch_helpers import dispatch_tool_calls
from kase.tools.registry import registry, discover_builtin_tools
from kase.toolsets import get_toolset, resolve_toolset, TOOLSETS
from kase.utils import get_kase_home, safe_json_loads
from kase.logging_setup import setup_logging


logger = logging.getLogger(__name__)


class AIAgent:
    """Kase AI Agent — the core conversation orchestrator."""

    def __init__(
        self,
        model: str = "",
        provider: str = "openai",
        api_key: str = None,
        base_url: str = None,
        api_mode: str = "chat_completions",
        max_iterations: int = 90,
        enabled_toolsets: Optional[List[str]] = None,
        disabled_toolsets: Optional[List[str]] = None,
        quiet_mode: bool = False,
        platform: str = "cli",
        session_id: str = None,
        skip_context_files: bool = False,
        skip_memory: bool = False,
        credential_pool: Optional[CredentialPool] = None,
        save_trajectories: bool = False,
        memory_manager: Optional[MemoryManager] = None,
        context_engine: Optional[ContextEngine] = None,
        callbacks: Optional[Dict[str, Callable]] = None,
        iteration_budget: Optional[IterationBudget] = None,
        system_message: Optional[str] = None,
        prefill_messages: Optional[List[Dict]] = None,
        model_router: Optional[ModelRouter] = None,
        multi_model_config: Optional[Dict] = None,
        long_term_memory: Optional[LongTermMemory] = None,
        **kwargs,
    ):
        self.model = model or os.getenv("KASE_MODEL", "gpt-4o")
        self.provider = provider or os.getenv("KASE_PROVIDER", "openai")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.api_mode = api_mode or os.getenv("KASE_API_MODE", "chat_completions")
        self.max_iterations = max_iterations
        self.quiet_mode = quiet_mode
        self.platform = platform
        self.session_id = session_id or f"kase_{uuid.uuid4().hex[:12]}"
        self.skip_context_files = skip_context_files
        self.skip_memory = skip_memory
        self.save_trajectories = save_trajectories
        self.system_message = system_message
        self.prefill_messages = prefill_messages or []
        self.callbacks = callbacks or {}

        self._kase_home = get_kase_home()
        self._credential_pool = credential_pool or CredentialPool()
        self._memory_manager = memory_manager or MemoryManager()
        self._context_engine = context_engine or ContextCompressor(context_length=128000)
        self._iteration_budget = iteration_budget or IterationBudget(max_total=max_iterations)
        self._interrupt_requested = False
        self._cached_system_prompt = ""
        self._api_call_count = 0
        self._tool_call_count = 0
        self._total_tokens = 0
        self._think_scrubber = StreamingThinkScrubber()
        self._budget_grace_call = True

        self._spinner = None
        self._session_db = None
        self._long_term_memory = long_term_memory
        self._analytics = None
        self._initialized = False

        self._enabled_toolsets = enabled_toolsets or ["kase-cli"]
        self._disabled_toolsets = disabled_toolsets or []
        self._messages: List[Dict] = []
        self._recent_tool_errors: List[str] = []

        self._model_router = model_router or ModelRouter(
            routes=multi_model_config
        )

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        if self._long_term_memory is None and os.getenv("KASE_LONG_TERM_MEMORY", "1") != "0":
            from kase.agent.long_term_memory import LongTermMemory
            self._long_term_memory = LongTermMemory()
        if self._analytics is None and os.getenv("KASE_ANALYTICS", "1") != "0":
            from kase.web_panel.analytics import AnalyticsTracker
            self._analytics = AnalyticsTracker()
        self._spinner = KawaiiSpinner(quiet=self.quiet_mode)
        setup_logging(f"agent_{self.session_id[:8]}")
        self._resolve_model()
        self._init_tools(self._enabled_toolsets, self._disabled_toolsets)
        self._init_client()
        self._memory_manager.initialize({"kase_home": self._kase_home})
        self._auto_learn_enabled = True
        mm = self._model_router.is_multi_model()
        logger.info(
            "Kase Agent initialized: model=%s provider=%s session=%s tools=%d multi_model=%s",
            self.model, self.provider, self.session_id, len(self.valid_tool_names), mm,
        )

    def _setup_logging(self) -> None:
        setup_logging(f"agent_{self.session_id[:8]}")

    @property
    def model_router(self) -> ModelRouter:
        return self._model_router

    def _resolve_model(self) -> None:
        if not self.model and os.getenv("KASE_MODEL"):
            self.model = os.getenv("KASE_MODEL")
        if not self.model:
            self.model = "gpt-4o"
        route = self._model_router.get_route(TASK_AGENTIC)
        self.context_length = route.context_length or get_model_context_length(self.model)
        self._context_engine.context_length = self.context_length
        self._model_router.active_task = TASK_AGENTIC

    def _init_tools(self, enabled: List[str], disabled: List[str]) -> None:
        discover_builtin_tools()

        resolved: Set[str] = set()
        composite_toolsets = {"kase-cli", "kase-messaging", "kase-telegram", "kase-discord"}

        for name in enabled:
            if name in composite_toolsets or name in TOOLSETS:
                resolved.update(get_toolset(name))
            else:
                resolved.add(name)

        for name in disabled:
            ts_tools = set(get_toolset(name))
            resolved -= ts_tools
            resolved.discard(name)

        self.valid_tool_names = resolved
        self.tool_schemas = registry.get_definitions(resolved)

        logger.info("Tools initialized: %d tools in %d schemas", len(resolved), len(self.tool_schemas))

    def _init_client(self) -> None:
        self._client = None
        route = self._model_router.get_route(TASK_AGENTIC)
        api_key = self.api_key or os.getenv(f"{route.provider.upper()}_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
        base_url = self.base_url or route.base_url or ""
        if api_key:
            try:
                import openai
                self._client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url or None,
                )
            except Exception as e:
                logger.warning("Failed to initialize LLM client: %s", e)

    def chat(self, message: str) -> str:
        """Simple interface — returns final response string."""
        result = self.run_conversation(message)
        return result.get("final_response", "")

    def run_conversation(
        self,
        user_message: str,
        system_message: str = None,
        conversation_history: List[Dict] = None,
        task_id: str = None,
    ) -> Dict:
        """Full interface — runs the conversation loop."""
        self._ensure_initialized()
        if system_message:
            self.system_message = system_message

        if conversation_history:
            self._messages = list(conversation_history)

        if user_message:
            self._messages.append({"role": "user", "content": user_message})

        self._build_system_prompt()
        self._budget_grace_call = True

        self._spinner.start()

        try:
            while (self._api_call_count < self.max_iterations
                   and self._iteration_budget.remaining > 0) or self._budget_grace_call:

                if self._interrupt_requested:
                    break

                self._budget_grace_call = False

                try:
                    response = self._call_llm()
                except Exception as e:
                    reason = classify_api_error(e, self.provider)
                    logger.error("LLM call failed: %s (reason=%s)", e, reason)

                    if should_retry(reason):
                        continue
                    if should_fallback(reason):
                        self._try_fallback()
                        continue

                    return {
                        "final_response": f"I encountered an error: {e}",
                        "messages": self._messages,
                        "error": str(e),
                    }

                self._api_call_count += 1

                if not response:
                    continue

                assistant_msg = {"role": "assistant", "content": response.get("content", "")}

                reasoning = response.get("reasoning", "")
                if reasoning:
                    assistant_msg["reasoning"] = reasoning

                tool_calls = response.get("tool_calls", [])
                if tool_calls:
                    assistant_msg["tool_calls"] = tool_calls
                    self._messages.append(assistant_msg)

                    tool_results = dispatch_tool_calls(tool_calls, task_id=task_id)
                    for tr in tool_results:
                        self._messages.append(tr)
                        self._tool_call_count += 1
                else:
                    self._messages.append(assistant_msg)

                    final = response.get("content", "")
                    self._spinner.stop()
                    self._auto_learn()

                    return {
                        "final_response": final,
                        "messages": self._messages,
                        "usage": response.get("usage", {}),
                        "api_calls": self._api_call_count,
                        "tool_calls": self._tool_call_count,
                    }

        except KeyboardInterrupt:
            self._interrupt_requested = True
            return {
                "final_response": "Interrupted by user.",
                "messages": self._messages,
                "interrupted": True,
            }
        finally:
            self._spinner.stop()
            self._auto_learn()

        self._auto_learn()
        return {
            "final_response": "Max iterations reached.",
            "messages": self._messages,
            "api_calls": self._api_call_count,
            "tool_calls": self._tool_call_count,
        }

    def _build_system_prompt(self) -> str:
        if self._cached_system_prompt:
            return self._cached_system_prompt

        prompt = build_system_prompt(self, self.system_message)
        self._cached_system_prompt = prompt

        if self._messages:
            has_system = any(
                isinstance(m, dict) and m.get("role") == "system"
                for m in self._messages
            )
            if not has_system:
                self._messages.insert(0, {"role": "system", "content": prompt})

        return prompt

    def _call_llm(self) -> Optional[Dict]:
        if not self._client and not self._model_router.is_multi_model():
            logger.warning("No LLM client available")
            return {"content": "I'm not configured with an API key yet.", "tool_calls": []}

        messages = self._sanitize_messages()
        tools = self.tool_schemas if self.tool_schemas else None

        task_type = self._model_router.active_task
        last_tool_name = self._detect_last_tool_name()
        if last_tool_name:
            detected = self._model_router.detect_task_type(tool_name=last_tool_name)
            if detected != TASK_AGENTIC:
                task_type = detected
                self._model_router.active_task = detected

        result = self._model_router.call_llm(
            messages=messages,
            task_type=task_type,
            tools=tools,
        )

        if result is None:
            if self._client:
                try:
                    response = self._client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        tools=tools or [],
                        stream=False,
                    )
                    choice = response.choices[0] if response.choices else None
                    if not choice:
                        return None
                    message = choice.message
                    result = {
                        "content": message.content or "",
                        "role": "assistant",
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
                except Exception as e:
                    err_str = str(e).lower()
                    if "context_length_exceeded" in err_str or "too many tokens" in err_str:
                        self._handle_context_overflow(e)
                        return None
                    logger.error("Primary LLM call failed: %s", e)
                    return None
            else:
                return None

        usage = result.get("usage", {})
        self._total_tokens += usage.get("total_tokens", 0)

        if usage:
            self._context_engine.update_from_response(usage)
            if self._context_engine.should_compress():
                self._messages = self._context_engine.compress(self._messages)

        if self._analytics:
            self._analytics.record_call(
                session_id=self.session_id,
                model=result.get("model") or self.model,
                provider=result.get("provider") or self.provider,
                task_type=result.get("task_type", self._model_router.active_task),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                success=True,
                tool_calls=len(result.get("tool_calls", [])),
                fallback_used=result.get("fallback_used", False),
            )

        return result

    def _sanitize_messages(self) -> List[Dict]:
        msgs = self._messages

        if any(msg.get("content") == self._cached_system_prompt for msg in msgs):
            pass
        elif self._cached_system_prompt:
            msgs = [{"role": "system", "content": self._cached_system_prompt}] + [
                m for m in msgs if m.get("role") != "system"
            ]

        msgs = _sanitize_messages_surrogates(msgs)

        route = self._model_router.get_route()
        ctx_len = route.context_length or self.context_length
        from kase.agent.model_metadata import estimate_messages_tokens_rough
        est_tokens = estimate_messages_tokens_rough(msgs)

        buffer = int(ctx_len * 0.1)
        if est_tokens > ctx_len - buffer:
            msgs = _strip_images_from_messages(msgs)

        return msgs

    def _handle_context_overflow(self, error: Exception) -> None:
        logger.warning("Context overflow, compressing with router summarizer")
        summary = self._model_router.summarize(
            json.dumps([m for m in self._messages[-20:]], ensure_ascii=False),
            max_tokens=1000,
        )
        if summary:
            self._messages = self._messages[:3] + [
                {"role": "system", "content": f"[Compressed context: {summary}]"}
            ]
        else:
            compressed = self._context_engine.compress(self._messages, focus_topic="compress")
            if compressed:
                self._messages = compressed

    def _try_fallback(self) -> bool:
        fallback_model = os.getenv("KASE_FALLBACK_MODEL", "")
        if not fallback_model:
            return False
        logger.info("Falling back to model: %s", fallback_model)
        self.model = fallback_model
        return True

    def _detect_last_tool_name(self) -> str:
        for m in reversed(self._messages):
            if m.get("role") == "assistant" and m.get("tool_calls"):
                for tc in m["tool_calls"]:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    if name:
                        return name
            if m.get("role") == "tool":
                continue
        return ""

    def _switch_task_mode(self, task_type: str) -> bool:
        if task_type in ALL_TASK_TYPES:
            self._model_router.active_task = task_type
            route = self._model_router.get_route(task_type)
            logger.info("Switched to %s mode: %s/%s", task_type, route.provider, route.model)
            return True
        return False

    def deep_think(self, question: str) -> str:
        route = self._model_router.get_route(TASK_REASONING)
        messages = [
            {"role": "system", "content": "You are a deep reasoning engine. Think step by step "
                                          "and provide thorough analysis. Show your reasoning process."},
            {"role": "user", "content": question},
        ]
        result = self._model_router.call_llm(messages, task_type=TASK_REASONING)
        if result:
            content = result.get("content", "")
            reasoning = result.get("reasoning", "")
            if reasoning:
                return f"<reasoning>\n{reasoning}\n</reasoning>\n\n{content}"
            return content
        return f"(Deep thinking unavailable for: {question})"

    def run_coding_task(self, task: str) -> Dict:
        result = self._model_router.call_coding_cli(task)
        if result.get("success"):
            return result
        route = self._model_router.get_route(TASK_CODING)
        messages = [
            {"role": "system", "content": "You are a coding expert. Write clean, correct, "
                                          "well-documented code."},
            {"role": "user", "content": task},
        ]
        llm_result = self._model_router.call_llm(messages, task_type=TASK_CODING)
        if llm_result:
            return {"success": True, "output": llm_result.get("content", ""),
                    "model": route.model, "provider": route.provider}
        return {"success": False, "error": "Coding task failed"}

    def _auto_learn(self) -> None:
        if not self._long_term_memory or not self._auto_learn_enabled:
            return
        if len(self._messages) < 2:
            return
        try:
            recent = self._messages[-6:]
            extracted = self._long_term_memory.extract_from_messages(recent, source="conversation")
            if extracted:
                logger.debug("Auto-learned %d new memories", len(extracted))
        except Exception as e:
            logger.debug("Auto-learn extraction failed: %s", e)

    def teach(self, content: str, memory_type: str = "fact",
              tags: Optional[List[str]] = None) -> str:
        if not self._long_term_memory:
            return "Long-term memory is disabled"
        return self._long_term_memory.store(content, memory_type, tags or [],
                                            source="user_command")

    def recall(self, query: str, limit: int = 5) -> List[Dict]:
        if not self._long_term_memory:
            return []
        return self._long_term_memory.recall(query, limit=limit)

    def forget(self, content: str = "", memory_id: str = "", memory_type: str = "") -> int:
        if not self._long_term_memory:
            return 0
        if memory_id:
            return 1 if self._long_term_memory.delete(memory_id) else 0
        if memory_type:
            return self._long_term_memory.delete_by_type(memory_type)
        if content:
            return self._long_term_memory.delete_by_content(content)
        return 0

    def get_learned_memories(self, memory_type: Optional[str] = None,
                              limit: int = 50) -> List[Dict]:
        if not self._long_term_memory:
            return []
        return self._long_term_memory.get_all(memory_type=memory_type, limit=limit)

    def interrupt(self) -> None:
        self._interrupt_requested = True

    def reset_session(self) -> None:
        self._messages = []
        self._api_call_count = 0
        self._tool_call_count = 0
        self._total_tokens = 0
        self._cached_system_prompt = ""
        self._interrupt_requested = False
        self._budget_grace_call = True
        self._recent_tool_errors = []
        self._context_engine.on_session_reset()
        self._model_router.active_task = TASK_AGENTIC
        logger.info("Session reset")

    @property
    def memory_manager(self) -> MemoryManager:
        return self._memory_manager

    @property
    def usage(self) -> Dict:
        return {
            "api_calls": self._api_call_count,
            "tool_calls": self._tool_call_count,
            "total_tokens": self._total_tokens,
            "model": self.model,
            "provider": self.provider,
        }

    def get_status(self) -> Dict:
        self._ensure_initialized()
        router_status = self._model_router.get_status()
        route = self._model_router.get_route()
        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "platform": self.platform,
            "api_calls": self._api_call_count,
            "tool_calls": self._tool_call_count,
            "total_tokens": self._total_tokens,
            "tools_enabled": len(self.valid_tool_names),
            "messages": len(self._messages),
            "multi_model": router_status,
            "active_mode": self._model_router.active_task,
            "active_mode_model": f"{route.provider}/{route.model}",
        }
