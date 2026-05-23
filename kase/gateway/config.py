"""Gateway configuration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PlatformConfig:
    enabled: bool = False
    token: str = ""
    toolsets: List[str] = field(default_factory=lambda: ["kase-messaging"])
    allowed_users: List[str] = field(default_factory=list)
    auto_approve: bool = False


@dataclass
class GatewayConfig:
    enabled: bool = False
    platform_configs: Dict[str, PlatformConfig] = field(default_factory=dict)
    model: str = ""
    provider: str = "openai"


DEFAULT_PLATFORMS = {
    "telegram",
    "discord",
    "slack",
    "whatsapp",
    "signal",
    "matrix",
    "web",
}


def load_gateway_config() -> GatewayConfig:
    from kase.cli.config import load_config
    config = load_config()
    gw = config.get("gateway", {})
    
    gw_config = GatewayConfig(
        enabled=gw.get("enabled", False),
        model=gw.get("model", ""),
        provider=gw.get("provider", ""),
    )
    
    for platform in DEFAULT_PLATFORMS:
        pc = gw.get(platform, {})
        gw_config.platform_configs[platform] = PlatformConfig(
            enabled=pc.get("enabled", False),
            token=pc.get("token", ""),
            toolsets=pc.get("toolsets", ["kase-messaging"]),
            allowed_users=pc.get("allowed_users", []),
            auto_approve=pc.get("auto_approve", False),
        )
    
    return gw_config
