"""OpenAI-compatible provider."""

import os
from kase.providers import registry
from kase.providers.base import ProviderProfile


registry.register_provider(ProviderProfile(
    name="openai",
    display_name="OpenAI",
    api_mode="chat_completions",
    base_url="https://api.openai.com/v1",
    env_key="OPENAI_API_KEY",
    models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "o1", "o3"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("OPENAI_API_KEY")),
))
