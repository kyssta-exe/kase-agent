import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="kilocode",
    display_name="Kilocode",
    api_mode="chat_completions",
    base_url="https://api.kilocode.ai/v1",
    env_key="KILOCODE_API_KEY",
    models=["kilocode-v1"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("KILOCODE_API_KEY")),
))
