"""Google Gemini provider."""

import os
from kase.providers import registry
from kase.providers.base import ProviderProfile


registry.register_provider(ProviderProfile(
    name="gemini",
    display_name="Google Gemini",
    api_mode="chat_completions",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    env_key="GEMINI_API_KEY",
    models=["gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    context_length=1048576,
    check_fn=lambda: bool(os.getenv("GEMINI_API_KEY")) or bool(os.getenv("GOOGLE_API_KEY")),
))
