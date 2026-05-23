"""Interactive setup wizard for Kase Agent."""

import importlib
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from kase.cli.config import get_config_path, load_config, save_config
from kase.providers import list_providers, ensure_providers_loaded
from kase.utils import get_kase_home

logger = logging.getLogger(__name__)

_PROMPT_OK = "\033[92m✓\033[0m"
_PROMPT_INFO = "\033[94mi\033[0m"
_PROMPT_WARN = "\033[93m!\033[0m"


def _ask(question: str, default: str = "", secret: bool = False) -> str:
    prompt = f"  {question}"
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    try:
        if secret:
            import getpass
            val = getpass.getpass(prompt)
        else:
            val = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return val if val else default


def _pick(options: List[str], title: str, default: str = "") -> str:
    print(f"\n  {title}")
    for i, opt in enumerate(options, 1):
        marker = " *" if opt == default else ""
        print(f"    {i}. {opt}{marker}")
    choice = _ask(f"Enter number (1-{len(options)})", default="1")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(options):
            return options[idx]
    except ValueError:
        pass
    return options[0] if not default else default


def setup_all():
    """Full interactive setup wizard."""
    print()
    print("  ╔══════════════════════════════════════╗")
    print("  ║       Kase Agent Setup Wizard        ║")
    print("  ╚══════════════════════════════════════╝")
    print()

    config = load_config()
    changed = False

    # Step 1: Provider + Model
    print(f"  {_PROMPT_INFO} Step 1: Choose a model provider")
    print(f"  {_PROMPT_INFO} Kase supports 31 providers (OpenAI, Anthropic, Gemini, Grok, etc.)")
    providers = list_providers()
    provider_names = sorted(p.get("name", "") for p in providers if p.get("name"))
    current_provider = config.get("provider", "openai")
    provider = _pick(provider_names, "Select provider:", default=current_provider)
    if provider != config.get("provider"):
        config["provider"] = provider
        changed = True

    # Step 2: API Key
    print(f"\n  {_PROMPT_INFO} Step 2: Set your API key")
    current_key = config.get("api_key", "") or os.getenv(f"{provider.upper()}_API_KEY", "")
    if current_key:
        masked = current_key[:8] + "..." if len(current_key) > 8 else "***"
        print(f"  Current key: {masked}")
        if _ask("Change it?", "n").lower() in ("y", "yes"):
            key = _ask(f"Enter your {provider} API key", secret=True)
            if key:
                config["api_key"] = key
                os.environ[f"{provider.upper()}_API_KEY"] = key
                changed = True
    else:
        key = _ask(f"Enter your {provider} API key", secret=True)
        if key:
            config["api_key"] = key
            os.environ[f"{provider.upper()}_API_KEY"] = key
            changed = True

    # Step 3: Base URL (optional)
    print(f"\n  {_PROMPT_INFO} Step 3: Base URL (optional)")
    print("  Leave blank to use the provider's default endpoint.")
    current_url = config.get("base_url", "")
    if current_url:
        print(f"  Current: {current_url}")
    url = _ask("Custom base URL", current_url)
    if url != current_url:
        config["base_url"] = url
        changed = True

    if changed:
        save_config(config)
        print(f"\n  {_PROMPT_OK} Configuration saved to {get_config_path()}")

    # Step 4: Verify
    print(f"\n  {_PROMPT_INFO} Step 4: Verify installation")
    print(f"  Provider: {config.get('provider', 'openai')}")
    has_key = bool(config.get("api_key") or os.getenv(f"{config.get('provider', 'openai').upper()}_API_KEY"))
    print(f"  API Key: {'\033[92mSet\033[0m' if has_key else '\033[93mNot set\033[0m'}")
    print()
    print(f"  {_PROMPT_OK} Setup complete! Run \033[1mkase\033[0m to start.")
    print()


def setup_model():
    """Configure model provider."""
    config = load_config()
    changed = False

    providers = list_providers()
    provider_names = sorted(p.get("name", "") for p in providers if p.get("name"))
    current_provider = config.get("provider", "openai")

    provider = _pick(provider_names, "Select provider:", default=current_provider)
    if provider != config.get("provider"):
        config["provider"] = provider
        changed = True

    # Optional model override
    current_model = config.get("model", "") or os.getenv("KASE_MODEL", "")
    if current_model:
        print(f"  Current model: {current_model}")
    model = _ask("Model (leave blank for provider default)", current_model)
    if model:
        config["model"] = model
        changed = True

    # API key
    env_var = f"{provider.upper()}_API_KEY"
    current_key = config.get("api_key", "") or os.getenv(env_var, "")
    if current_key:
        masked = current_key[:8] + "..."
        print(f"  API key: {masked}")
        if _ask("Change?", "n").lower() in ("y", "yes"):
            key = _ask(f"Enter {provider} API key", secret=True)
            if key:
                config["api_key"] = key
                os.environ[env_var] = key
                changed = True
    else:
        key = _ask(f"Enter {provider} API key", secret=True)
        if key:
            config["api_key"] = key
            os.environ[env_var] = key
            changed = True

    current_url = config.get("base_url", "")
    url = _ask("Custom base URL (or blank for default)", current_url)
    if url != current_url:
        config["base_url"] = url
        changed = True

    if changed:
        save_config(config)
        print(f"  {_PROMPT_OK} Model config saved")
    else:
        print("  No changes made")


def setup_msg():
    """Configure messaging platforms."""
    config = load_config()
    messaging = config.setdefault("messaging", {})
    changed = False

    platforms = {
        "telegram": ("TELEGRAM_BOT_TOKEN", "Bot token from @BotFather"),
        "discord": ("DISCORD_BOT_TOKEN", "Bot token from Discord Developer Portal"),
        "slack": ("SLACK_BOT_TOKEN", "Bot token from Slack API"),
        "whatsapp": ("WHATSAPP_API_KEY", "WhatsApp Business API key"),
    }

    print(f"\n  {_PROMPT_INFO} Configure messaging platforms")
    print("  Kase can listen on Telegram, Discord, Slack, WhatsApp, and more.")
    print("  You can configure these later — they are optional.")
    print()

    for platform, (env_key, hint) in sorted(platforms.items()):
        current = messaging.get(platform, {})
        enabled = current.get("enabled", False)
        token = current.get("token", "") or os.getenv(env_key, "")

        print(f"  [{'+' if enabled else ' '}] {platform.capitalize()}")
        if _ask(f"  Enable {platform}?", "y" if enabled else "n").lower() in ("y", "yes"):
            if not token:
                token = _ask(f"  Enter {env_key}", secret=True)
            if token:
                messaging[platform] = {"enabled": True, "token": token, "env_key": env_key}
                os.environ[env_key] = token
                changed = True
        else:
            if platform in messaging:
                del messaging[platform]
                changed = True
        print()

    if changed:
        config["messaging"] = messaging
        save_config(config)
        print(f"  {_PROMPT_OK} Messaging config saved")
        print(f"  {_PROMPT_INFO} Run \033[1mkase gateway\033[0m to start the messaging gateway")
    else:
        print("  No changes made")
