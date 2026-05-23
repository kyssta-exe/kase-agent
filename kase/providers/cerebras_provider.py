import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="cerebras",
    display_name="Cerebras",
    api_mode="chat_completions",
    base_url="https://api.cerebras.ai/v1",
    env_key="CEREBRAS_API_KEY",
    models=["cerebras-nova", "llama3.1-8b", "llama3.1-70b"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("CEREBRAS_API_KEY")),
))
