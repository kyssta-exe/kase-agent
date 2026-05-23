import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="cohere",
    display_name="Cohere",
    api_mode="chat_completions",
    base_url="https://api.cohere.com/v2",
    env_key="COHERE_API_KEY",
    models=["command-r", "command-r-plus", "command-a"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("COHERE_API_KEY")),
))
