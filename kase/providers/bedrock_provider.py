"""AWS Bedrock provider."""

import os
from kase.providers import registry
from kase.providers.base import ProviderProfile


def check_bedrock():
    return bool(os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_PROFILE"))


registry.register_provider(ProviderProfile(
    name="bedrock",
    display_name="AWS Bedrock",
    api_mode="chat_completions",
    base_url="",
    env_key="AWS_ACCESS_KEY_ID",
    models=["claude-3-5-sonnet", "claude-3-opus", "llama-3", "mistral-large"],
    context_length=200000,
    check_fn=check_bedrock,
))
