import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="octoai",
    display_name="OctoAI",
    api_mode="chat_completions",
    base_url="https://text.octoai.run/v1",
    env_key="OCTOAI_API_KEY",
    models=["meta-llama-3.1-70b", "mistral-7b", "codestral"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("OCTOAI_API_KEY")),
))
