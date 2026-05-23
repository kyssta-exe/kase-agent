import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="nvidia",
    display_name="NVIDIA NIM",
    api_mode="chat_completions",
    base_url="https://integrate.api.nvidia.com/v1",
    env_key="NVIDIA_API_KEY",
    models=["meta/llama-3.3-70b", "mistralai/mixtral-8x22b", "nvidia/llama-3.1-nemotron"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("NVIDIA_API_KEY")),
))
