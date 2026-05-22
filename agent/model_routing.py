"""Multi-model routing for Kase.

Enables per-category model/provider selection for 4 categories:
- reasoning  (deep thinking, complex analysis)
- research   (web search, information gathering)
- coding     (code generation, debugging, file operations)
- agentic    (general agentic tasks, tool orchestration)

Each category can have its own provider, model, base_url, and api_key.
Falls back gracefully: category -> default -> main model provider.
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

CATEGORIES = ("reasoning", "research", "coding", "agentic")

ModelRoute = Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]
"""Returns (provider, model, base_url, api_key).  None/empty = use main."""


def get_category_config(category: str) -> Dict[str, Any]:
    """Read model_routing.<category> from config."""
    if category not in CATEGORIES:
        return {}
    try:
        from kase_cli.config import load_config
        config = load_config()
    except ImportError:
        return {}
    routing = config.get("model_routing", {}) if isinstance(config, dict) else {}
    if not routing.get("enabled", False):
        return {}
    return routing.get(category, {}) if isinstance(routing, dict) else {}


def resolve_route(category: str) -> ModelRoute:
    """Resolve model route for a given task category.

    Resolution order:
    1. model_routing.<category>.provider+model+base_url+api_key
    2. model_routing.default.provider+model+base_url+api_key
    3. (None, None, None, None) -- caller uses main model

    Returns (provider, model, base_url, api_key).
    """
    cat_cfg = get_category_config(category)
    if cat_cfg:
        provider = cat_cfg.get("provider") or ""
        model = cat_cfg.get("model") or ""
        base_url = cat_cfg.get("base_url") or ""
        api_key = cat_cfg.get("api_key") or ""
        if provider or model:
            return (provider, model, base_url, api_key)

    # Fallback to model_routing.default
    try:
        from kase_cli.config import load_config
        config = load_config()
    except ImportError:
        return (None, None, None, None)
    routing = config.get("model_routing", {}) if isinstance(config, dict) else {}
    if isinstance(routing, dict):
        default_cfg = routing.get("default", {})
        if isinstance(default_cfg, dict):
            provider = default_cfg.get("provider") or ""
            model = default_cfg.get("model") or ""
            base_url = default_cfg.get("base_url") or ""
            api_key = default_cfg.get("api_key") or ""
            if provider or model:
                return (provider, model, base_url, api_key)

    return (None, None, None, None)


def format_route(category: str) -> str:
    """Human-readable description of the resolved route."""
    provider, model, base_url, api_key = resolve_route(category)
    parts = []
    if provider:
        parts.append(f"provider={provider}")
    if model:
        parts.append(f"model={model}")
    if not parts:
        return f"{category}: (main model)"
    return f"{category}: {', '.join(parts)}"
