"""OpenRouter provider."""

import os
from kase.providers import registry
from kase.providers.base import ProviderProfile


registry.register_provider(ProviderProfile(
    name="openrouter",
    display_name="OpenRouter",
    api_mode="chat_completions",
    base_url="https://openrouter.ai/api/v1",
    env_key="OPENROUTER_API_KEY",
    models=[],  # OpenRouter supports many models
    context_length=128000,
    check_fn=lambda: bool(os.getenv("OPENROUTER_API_KEY")),
))
