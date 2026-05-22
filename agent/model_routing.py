"""Multi-model routing for Kase.

Enables per-category model/provider selection with fallback chains.
Modes:
  - Classic   (single model) — uses the main model for everything
  - Adaptive  (multi-model)  — routes each task category to its own model

Categories:
  - reasoning        (deep thinking, complex analysis)
  - research         (web search, information gathering)
  - coding           (code generation, debugging, file operations)
  - agentic          (general agentic tasks, tool orchestration)
  - image_generation (image generation via supported providers)

Fallback chain for each category:
  1. category.model
  2. category.fallback.model
  3. default.model
  4. fallback_unified.model
  5. main model (None, None, None, None)
"""

import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

CATEGORIES = ("reasoning", "research", "coding", "agentic", "image_generation")

# Mode display names
MODE_CLASSIC = "classic"
MODE_ADAPTIVE = "adaptive"
MODE_LABELS = {
    MODE_CLASSIC: "Classic",
    MODE_ADAPTIVE: "Adaptive",
}

ModelRoute = Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]
"""Returns (provider, model, base_url, api_key).  None/empty = use main."""


def _get_routing_config() -> Dict[str, Any]:
    """Get the model_routing section from config, or empty dict."""
    try:
        from kase_cli.config import load_config
        config = load_config()
    except ImportError:
        return {}
    if not isinstance(config, dict):
        return {}
    routing = config.get("model_routing", {})
    return routing if isinstance(routing, dict) else {}


def get_mode() -> str:
    """Return the current mode: 'classic' or 'adaptive'."""
    routing = _get_routing_config()
    if routing.get("enabled", False):
        return MODE_ADAPTIVE
    return MODE_CLASSIC


def get_mode_label() -> str:
    """Return the human-readable mode label."""
    return MODE_LABELS.get(get_mode(), "Classic")


def is_adaptive() -> bool:
    """True if Adaptive (multi-model) mode is active."""
    return get_mode() == MODE_ADAPTIVE


def _read_entry(cfg: Any) -> ModelRoute:
    """Extract (provider, model, base_url, api_key) from a config dict."""
    if not isinstance(cfg, dict):
        return ("", "", "", "")
    return (
        cfg.get("provider") or "",
        cfg.get("model") or "",
        cfg.get("base_url") or "",
        cfg.get("api_key") or "",
    )


def _has_route(entry: ModelRoute) -> bool:
    """True if the entry has at least a provider or model set."""
    provider, model, _base_url, _api_key = entry
    return bool(provider) or bool(model)


def resolve_route(category: str) -> ModelRoute:
    """Resolve model route for a given task category.

    Resolution order (returns first match):
      1. model_routing.<category>.provider+model
      2. model_routing.<category>.fallback.provider+model
      3. model_routing.default.provider+model
      4. model_routing.fallback_unified.provider+model
      5. (None, None, None, None)  — caller uses main model

    Returns (provider, model, base_url, api_key).
    """
    routing = _get_routing_config()
    if not routing.get("enabled", False):
        return (None, None, None, None)

    category_entry = routing.get(category, {}) if isinstance(category, str) else {}
    if isinstance(category_entry, dict):
        # Step 1: category primary
        route = _read_entry(category_entry)
        if _has_route(route):
            return route

        # Step 2: category fallback
        fallback = category_entry.get("fallback", {})
        route = _read_entry(fallback)
        if _has_route(route):
            return route

    # Step 3: default
    default_entry = routing.get("default", {})
    route = _read_entry(default_entry)
    if _has_route(route):
        return route

    # Step 4: unified fallback
    unified = routing.get("fallback_unified", {})
    route = _read_entry(unified)
    if _has_route(route):
        return route

    # Step 5: main model
    return (None, None, None, None)


def resolve_with_fallback_chain(category: str) -> list[ModelRoute]:
    """Return the full fallback chain for a category (all steps, including empty).

    Useful for UI display of the resolution path.
    """
    routing = _get_routing_config()
    chain: list[ModelRoute] = []

    if not routing.get("enabled", False):
        return chain

    category_entry = routing.get(category, {}) if isinstance(category, str) else {}
    if isinstance(category_entry, dict):
        chain.append(("category", *_read_entry(category_entry)))
        fallback = category_entry.get("fallback", {})
        chain.append(("fallback", *_read_entry(fallback)))

    default_entry = routing.get("default", {})
    chain.append(("default", *_read_entry(default_entry)))

    unified = routing.get("fallback_unified", {})
    chain.append(("fallback_unified", *_read_entry(unified)))

    chain.append(("main", None, None, None, None))
    return chain


def format_route(category: str) -> str:
    """Human-readable description of the resolved route."""
    if not is_adaptive():
        return f"{category}: (Classic mode — main model)"
    provider, model, base_url, api_key = resolve_route(category)
    parts = []
    if provider:
        parts.append(f"provider={provider}")
    if model:
        parts.append(f"model={model}")
    if not parts:
        return f"{category}: (main model)"
    return f"{category}: {', '.join(parts)}"


def format_mode_status() -> str:
    """Return a one-liner describing the current routing mode."""
    mode = get_mode()
    label = get_mode_label()
    if mode == MODE_CLASSIC:
        return f"{label} mode — single model for all tasks"
    categories_active = sum(
        1 for c in CATEGORIES if _has_route(_read_entry(_get_routing_config().get(c, {})))
    )
    return f"{label} mode — {categories_active}/{len(CATEGORIES)} categories routed"
