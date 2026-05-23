import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="alibaba",
    display_name="Alibaba (Qwen)",
    api_mode="chat_completions",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    env_key="ALIBABA_API_KEY",
    models=["qwen-max", "qwen-plus", "qwen-turbo", "qwen2.5-72b"],
    context_length=131072,
    check_fn=lambda: bool(os.getenv("ALIBABA_API_KEY") or os.getenv("DASHSCOPE_API_KEY")),
))
