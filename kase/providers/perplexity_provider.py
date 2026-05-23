import os
from kase.providers import registry
from kase.providers.base import ProviderProfile

registry.register_provider(ProviderProfile(
    name="perplexity",
    display_name="Perplexity",
    api_mode="chat_completions",
    base_url="https://api.perplexity.ai",
    env_key="PERPLEXITY_API_KEY",
    models=["sonar-pro", "sonar", "sonar-deep-research"],
    context_length=200000,
    check_fn=lambda: bool(os.getenv("PERPLEXITY_API_KEY")),
))
