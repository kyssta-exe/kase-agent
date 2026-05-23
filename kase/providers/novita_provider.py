import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="novita",
    display_name="Novita AI",
    api_mode="chat_completions",
    base_url="https://api.novita.ai/v1",
    env_key="NOVITA_API_KEY",
    models=["meta-llama/llama-3.3-70b", "deepseek/deepseek-v3"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("NOVITA_API_KEY")),
))
