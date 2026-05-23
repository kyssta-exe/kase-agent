import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="deepinfra",
    display_name="DeepInfra",
    api_mode="chat_completions",
    base_url="https://api.deepinfra.com/v1/openai",
    env_key="DEEPINFRA_API_KEY",
    models=["meta-llama/Llama-3.3-70B", "deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("DEEPINFRA_API_KEY")),
))
