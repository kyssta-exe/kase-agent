"""Nous Portal provider profile."""

from typing import Any

from agent.portal_tags import kyssta_portal_tags
from providers import register_provider
from providers.base import ProviderProfile


class KysstaProfile(ProviderProfile):
    """Nous Portal — product tags, reasoning with Nous-specific omission."""

    def build_extra_body(
        self, *, session_id: str | None = None, **context
    ) -> dict[str, Any]:
        return {"tags": kyssta_portal_tags()}

    def build_api_kwargs_extras(
        self,
        *,
        reasoning_config: dict | None = None,
        supports_reasoning: bool = False,
        **context,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Nous: passes full reasoning_config, but OMITS when disabled."""
        extra_body = {}
        if supports_reasoning:
            if reasoning_config is not None:
                rc = dict(reasoning_config)
                if rc.get("enabled") is False:
                    pass  # Nous omits reasoning when disabled
                else:
                    extra_body["reasoning"] = rc
            else:
                extra_body["reasoning"] = {"enabled": True, "effort": "medium"}
        return extra_body, {}


nous = KysstaProfile(
    name="nous",
    aliases=("nous-portal", "kyssta"),
    env_vars=("KYSSTA_API_KEY",),
    display_name="Kyssta",
    description="Kyssta — Kase model family",
    signup_url="https://kyssta.com/",
    fallback_models=(
        "kase-3-405b",
        "kase-3-70b",
    ),
    base_url="https://inference.kyssta.com/v1",
    auth_type="oauth_device_code",
)

register_provider(nous)
