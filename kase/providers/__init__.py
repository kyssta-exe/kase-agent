"""Provider system for Kase Agent."""

import importlib
import logging
import os
from typing import Optional

from kase.providers.base import ProviderRegistry, ProviderProfile, BaseLLMProvider

logger = logging.getLogger(__name__)

registry = ProviderRegistry()

_PROVIDER_MODULES = [
    "openai_provider", "anthropic_provider", "gemini_provider",
    "bedrock_provider", "deepseek_provider", "openrouter_provider",
    "groq_provider", "grok_provider", "perplexity_provider",
    "together_provider", "fireworks_provider", "cohere_provider",
    "huggingface_provider", "replicate_provider", "mistral_provider",
    "azure_provider", "vertex_provider", "sambanova_provider",
    "cerebras_provider", "anyscale_provider", "octoai_provider",
    "deepinfra_provider", "lepton_provider", "stability_provider",
    "nvidia_provider", "xai_provider", "ai21_provider",
    "novita_provider", "minimax_provider", "alibaba_provider",
    "kilocode_provider",
]

_loaded = False


def ensure_providers_loaded():
    global _loaded
    if _loaded:
        return
    for mod_name in _PROVIDER_MODULES:
        try:
            importlib.import_module(f"kase.providers.{mod_name}")
        except Exception as e:
            logger.debug("Provider %s not available: %s", mod_name, e)
    _loaded = True


def get_provider(name: str) -> Optional[ProviderProfile]:
    ensure_providers_loaded()
    return registry.get_provider(name)


def list_providers():
    ensure_providers_loaded()
    return registry.list_providers()


def get_provider_by_model(model: str) -> Optional[ProviderProfile]:
    ensure_providers_loaded()
    return registry.get_provider_by_model(model)
