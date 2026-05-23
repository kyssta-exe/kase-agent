import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

def check_azure():
    return bool(os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"))

registry.register_provider(ProviderProfile(
    name="azure",
    display_name="Azure OpenAI",
    api_mode="chat_completions",
    base_url=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
    env_key="AZURE_OPENAI_API_KEY",
    models=["gpt-4o", "gpt-4-turbo", "gpt-35-turbo"],
    context_length=128000,
    check_fn=check_azure,
))
