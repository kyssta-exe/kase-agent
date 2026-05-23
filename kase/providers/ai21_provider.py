import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="ai21",
    display_name="AI21 Labs",
    api_mode="chat_completions",
    base_url="https://api.ai21.com/v1",
    env_key="AI21_API_KEY",
    models=["jamba-1.5", "jamba-1.5-mini"],
    context_length=256000,
    check_fn=lambda: bool(os.getenv("AI21_API_KEY")),
))
