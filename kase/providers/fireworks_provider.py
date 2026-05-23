import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="fireworks",
    display_name="Fireworks AI",
    api_mode="chat_completions",
    base_url="https://api.fireworks.ai/inference/v1",
    env_key="FIREWORKS_API_KEY",
    models=["accounts/fireworks/models/llama-v3p3-70b", "accounts/fireworks/models/deepseek-v3"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("FIREWORKS_API_KEY")),
))
