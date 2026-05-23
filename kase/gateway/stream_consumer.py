"""Async stream consumer bridging agent callbacks to platform delivery."""

import json
import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class StreamConsumer:
    def __init__(self, send_fn: Callable):
        self._send = send_fn
        self._buffer = ""
        self._edit_interval = 0.5

    def on_delta(self, chunk: str) -> None:
        self._buffer += chunk

    def on_complete(self, final: str) -> None:
        self._send(final)

    def on_error(self, error: str) -> None:
        logger.error("Stream error: %s", error)
        self._send(f"Error: {error}")

    def flush(self) -> str:
        buf = self._buffer
        self._buffer = ""
        return buf
