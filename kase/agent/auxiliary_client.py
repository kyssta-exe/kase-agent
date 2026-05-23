"""Auxiliary client for side tasks like compression, vision, title gen."""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AuxiliaryClient:
    def __init__(self, config: Optional[dict] = None):
        self._config = config or {}
        self._unhealthy_providers: dict = {}

    def summarize(self, text: str, max_tokens: int = 500) -> Optional[str]:
        try:
            import openai
            client = openai.OpenAI(
                api_key=self._config.get("api_key", ""),
                base_url=self._config.get("base_url", ""),
            )
            response = client.chat.completions.create(
                model=self._config.get("model", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "Summarize the following content concisely."},
                    {"role": "user", "content": text[:10000]},
                ],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning("Auxiliary summarization failed: %s", e)
            return None

    def is_provider_healthy(self, provider: str) -> bool:
        if provider in self._unhealthy_providers:
            import time
            if time.monotonic() - self._unhealthy_providers[provider] < 600:
                return False
            del self._unhealthy_providers[provider]
        return True

    def mark_unhealthy(self, provider: str) -> None:
        import time
        self._unhealthy_providers[provider] = time.monotonic()


def set_runtime_main(client: Any) -> None:
    pass
