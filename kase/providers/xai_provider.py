import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="xai",
    display_name="xAI",
    api_mode="chat_completions",
    base_url="https://api.x.ai/v1",
    env_key="XAI_API_KEY",
    models=["grok-2", "grok-2-mini"],
    context_length=131072,
    check_fn=lambda: bool(os.getenv("XAI_API_KEY")),
))
