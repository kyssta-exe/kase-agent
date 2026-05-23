import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="anyscale",
    display_name="Anyscale",
    api_mode="chat_completions",
    base_url="https://api.endpoints.anyscale.com/v1",
    env_key="ANYSCALE_API_KEY",
    models=["meta-llama/Llama-3.3-70B", "mistralai/Mixtral-8x22B"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("ANYSCALE_API_KEY")),
))
