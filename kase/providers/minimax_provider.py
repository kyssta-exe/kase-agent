import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="minimax",
    display_name="MiniMax",
    api_mode="chat_completions",
    base_url="https://api.minimax.chat/v1",
    env_key="MINIMAX_API_KEY",
    models=["MiniMax-Text-01", "abab6.5s"],
    context_length=1048576,
    check_fn=lambda: bool(os.getenv("MINIMAX_API_KEY")),
))
