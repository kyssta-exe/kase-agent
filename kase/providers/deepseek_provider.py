"""DeepSeek provider."""

import os
from kase.providers import registry
from kase.providers.base import ProviderProfile


registry.register_provider(ProviderProfile(
    name="deepseek",
    display_name="DeepSeek",
    api_mode="chat_completions",
    base_url="https://api.deepseek.com/v1",
    env_key="DEEPSEEK_API_KEY",
    models=["deepseek-chat", "deepseek-reasoner"],
    context_length=65536,
    check_fn=lambda: bool(os.getenv("DEEPSEEK_API_KEY")),
))
