import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="lepton",
    display_name="Lepton AI",
    api_mode="chat_completions",
    base_url="https://api.lepton.ai/v1",
    env_key="LEPTON_API_KEY",
    models=["llama3-70b", "mixtral-8x7b", "deepseek-v3"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("LEPTON_API_KEY")),
))
