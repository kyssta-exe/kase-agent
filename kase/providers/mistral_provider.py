import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="mistral",
    display_name="Mistral AI",
    api_mode="chat_completions",
    base_url="https://api.mistral.ai/v1",
    env_key="MISTRAL_API_KEY",
    models=["mistral-large", "mistral-small", "codestral", "ministral-8b"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("MISTRAL_API_KEY")),
))
