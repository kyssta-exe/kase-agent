"""Configuration management for Kase CLI."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


DEFAULT_CONFIG: Dict[str, Any] = {
    "_config_version": 2,
    "model": "",
    "provider": "openai",
    "api_mode": "chat_completions",
    "base_url": "",
    "api_key": "",
    "max_iterations": 90,
    "enabled_toolsets": ["kase-cli"],
    "disabled_toolsets": [],
    "quiet_mode": False,
    "save_trajectories": False,
    "terminal": {
        "cwd": "",
    },
    "display": {
        "skin": "default",
        "tool_preview_length": 120,
        "theme": "dark",
    },
    "security": {
        "redact_secrets": True,
        "dangerous_command_approval": True,
    },
    "delegation": {
        "max_concurrent_children": 3,
        "max_spawn_depth": 2,
        "child_timeout_seconds": 600,
        "orchestrator_enabled": True,
    },
    "compression": {
        "enabled": True,
        "threshold_percent": 0.75,
    },
    "multi_model": {
        "enabled": False,
        "routes": {
            "agentic": {"model": "gpt-4o", "provider": "openai", "context_length": 128000},
            "reasoning": {"model": "o1", "provider": "openai", "context_length": 200000, "temperature": 1.0},
            "summary": {"model": "gpt-4o-mini", "provider": "openai", "context_length": 128000, "temperature": 0.3},
            "coding": {"model": "gpt-4o", "provider": "openai", "context_length": 128000},
            "image_gen": {"model": "dall-e-3", "provider": "openai", "context_length": 128000},
        },
        "fallbacks": {
            "agentic": [{"model": "gpt-4o-mini", "provider": "openai"}],
            "reasoning": [{"model": "gpt-4o", "provider": "openai"}, {"model": "gpt-4o-mini", "provider": "openai"}],
            "summary": [{"model": "gpt-4o-mini", "provider": "openai"}],
            "coding": [{"model": "gpt-4o", "provider": "openai"}, {"model": "gpt-4o-mini", "provider": "openai"}],
            "image_gen": [],
        },
        "cli_tools": {
            "coding": [
                {"name": "opencode", "command": "opencode"},
                {"name": "gemini", "command": "gemini"},
                {"name": "claude", "command": "claude"},
                {"name": "aider", "command": "aider"},
            ],
        },
    },
}


def get_config_path() -> Path:
    kase_home = Path(os.getenv("KASE_HOME", Path.home() / ".kase"))
    return kase_home / "config.yaml"


def load_config() -> Dict[str, Any]:
    import yaml
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()
    
    if config_path.exists():
        try:
            user_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            if isinstance(user_config, dict):
                _deep_merge(config, user_config)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to load config: %s", e)
    
    return config


def save_config(config: Dict[str, Any]) -> None:
    import yaml
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _deep_merge(base: Dict, override: Dict) -> None:
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
