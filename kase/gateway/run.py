"""Gateway runner — multi-platform async agent."""

import asyncio
import logging
from typing import Optional

from kase.agent.core import AIAgent
from kase.gateway.config import GatewayConfig, load_gateway_config
from kase.gateway.session import SessionStore

logger = logging.getLogger(__name__)


class GatewayRunner:
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or load_gateway_config()
        self.session_store = SessionStore()
        self._running = False
        self._agents: dict = {}

    def start(self) -> None:
        if not self.config.enabled:
            logger.info("Gateway is not enabled")
            return
        
        self._running = True
        logger.info("Gateway starting with platforms: %s",
                     ", ".join(p for p, c in self.config.platform_configs.items() if c.enabled))
        
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                import threading
                t = threading.Thread(target=lambda: asyncio.run(self._run_forever()), daemon=True)
                t.start()
                return
        except RuntimeError:
            pass
        asyncio.run(self._run_forever())

    def _get_agent(self, session_key: str) -> AIAgent:
        if session_key not in self._agents:
            self._agents[session_key] = AIAgent(
                model=self.config.model,
                provider=self.config.provider,
                platform="gateway",
            )
        return self._agents[session_key]

    async def _run_forever(self) -> None:
        logger.info("Gateway running")
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Gateway stopped")

    def stop(self) -> None:
        self._running = False
        logger.info("Gateway stopping...")

    def handle_message(self, platform: str, chat_id: str, user_id: str, text: str) -> str:
        from kase.gateway.session import SessionSource, make_session_key
        source = SessionSource(platform=platform, chat_id=chat_id, user_id=user_id)
        key = make_session_key(source)
        agent = self._get_agent(key)
        return agent.chat(text)


def run_gateway():
    runner = GatewayRunner()
    runner.start()
