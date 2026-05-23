import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="replicate",
    display_name="Replicate",
    api_mode="chat_completions",
    base_url="https://api.replicate.com/v1",
    env_key="REPLICATE_API_KEY",
    models=["meta/meta-llama-3-70b", "mistralai/mixtral-8x7b"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("REPLICATE_API_KEY")),
))
