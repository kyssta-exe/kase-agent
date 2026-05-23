"""Anthropic Claude provider."""

import os
from kase.providers import registry
from kase.providers.base import ProviderProfile


def check_anthropic():
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return True
    try:
        from kase.agent.credential_pool import CredentialPool
        pool = CredentialPool()
        return pool.get_api_key("ANTHROPIC_API_KEY") is not None
    except Exception:
        return False


registry.register_provider(ProviderProfile(
    name="anthropic",
    display_name="Anthropic Claude",
    api_mode="chat_completions",
    base_url="https://api.anthropic.com/v1",
    env_key="ANTHROPIC_API_KEY",
    models=["claude-3-5-sonnet", "claude-3-opus", "claude-3-haiku",
            "claude-4-sonnet", "claude-4-opus"],
    context_length=200000,
    check_fn=check_anthropic,
))
