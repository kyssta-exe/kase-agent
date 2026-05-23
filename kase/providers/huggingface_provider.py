import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="huggingface",
    display_name="Hugging Face",
    api_mode="chat_completions",
    base_url="https://api-inference.huggingface.co/v1",
    env_key="HF_TOKEN",
    models=["meta-llama/Llama-3.3-70B-Instruct", "microsoft/Phi-4"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")),
))
