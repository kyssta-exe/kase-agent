import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="together",
    display_name="Together AI",
    api_mode="chat_completions",
    base_url="https://api.together.xyz/v1",
    env_key="TOGETHER_API_KEY",
    models=["meta-llama/Llama-3.3-70B", "mistralai/Mixtral-8x22B", "deepseek-ai/DeepSeek-V3"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("TOGETHER_API_KEY")),
))
