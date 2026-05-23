import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="sambanova",
    display_name="SambaNova",
    api_mode="chat_completions",
    base_url="https://api.sambanova.ai/v1",
    env_key="SAMBANOVA_API_KEY",
    models=["Meta-Llama-3.3-70B", "DeepSeek-R1-671B", "Qwen2.5-72B"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("SAMBANOVA_API_KEY")),
))
