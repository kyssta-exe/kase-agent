import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="groq",
    display_name="Groq",
    api_mode="chat_completions",
    base_url="https://api.groq.com/openai/v1",
    env_key="GROQ_API_KEY",
    models=["llama-3.3-70b", "llama-3.1-8b", "mixtral-8x7b", "gemma2-9b"],
    context_length=128000,
    check_fn=lambda: bool(os.getenv("GROQ_API_KEY")),
))
