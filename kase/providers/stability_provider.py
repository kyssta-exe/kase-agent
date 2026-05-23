import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="stability",
    display_name="Stability AI",
    api_mode="chat_completions",
    base_url="https://api.stability.ai/v1",
    env_key="STABILITY_API_KEY",
    models=["stable-diffusion-3.5", "stable-image-ultra"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("STABILITY_API_KEY")),
))
