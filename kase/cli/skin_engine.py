"""Kase skin/theme engine."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SkinConfig:
    name: str
    description: str = ""
    colors: Dict[str, str] = field(default_factory=dict)
    spinner: Dict = field(default_factory=dict)
    branding: Dict[str, str] = field(default_factory=dict)
    tool_prefix: str = "┊"
    tool_emojis: Dict[str, str] = field(default_factory=dict)


_BUILTIN_SKINS: Dict[str, dict] = {
    "default": {
        "name": "default",
        "description": "Classic Kase — elegant gold",
        "colors": {
            "banner_border": "#FFD700",
            "banner_title": "#FFA500",
            "banner_accent": "#FFD700",
            "banner_dim": "#888888",
            "banner_text": "#FFFFFF",
            "response_border": "#FFD700",
            "session_label": "#B8A0FF",
            "session_border": "#78788C",
            "ui_error": "#FF5555",
            "ui_ok": "#50FA7B",
        },
        "spinner": {
            "waiting_faces": ["(◕‿◕)", "(◡‿◡)", "(◕‿◕✿)"],
            "thinking_faces": ["(｡•᎔•｡)", "(｡•́︿•̀｡)", "◕‸◕"],
            "thinking_verbs": ["thinking", "processing", "analyzing", "computing"],
        },
        "branding": {
            "agent_name": "Kase",
            "welcome": "Kase Agent — The future of AI assistance, today.",
            "response_label": " ✦ Kase ✦ ",
            "prompt_symbol": "✦ ",
        },
        "tool_prefix": "┊",
    },
    "kyssta": {
        "name": "kyssta",
        "description": "Kyssta brand — deep purple and gold",
        "colors": {
            "banner_border": "#9B59B6",
            "banner_title": "#F1C40F",
            "banner_accent": "#9B59B6",
            "banner_dim": "#7F8C8D",
            "banner_text": "#ECF0F1",
            "response_border": "#9B59B6",
        },
        "branding": {
            "agent_name": "Kase by Kyssta",
            "response_label": " ⚡ Kase ⚡ ",
            "prompt_symbol": "⚡ ",
        },
        "tool_prefix": "▏",
    },
    "mono": {
        "name": "mono",
        "description": "Clean grayscale monochrome",
        "colors": {
            "banner_border": "#AAAAAA",
            "banner_title": "#CCCCCC",
            "banner_accent": "#999999",
            "banner_dim": "#666666",
            "banner_text": "#EEEEEE",
            "response_border": "#AAAAAA",
        },
        "spinner": {
            "thinking_faces": ["( )", "( )", "( )"],
            "thinking_verbs": [".", "..", "..."],
        },
        "branding": {
            "agent_name": "Kase",
            "response_label": " Kase ",
            "prompt_symbol": "> ",
        },
    },
}

_active_skin: Optional[SkinConfig] = None


def init_skin_from_config(config: dict) -> SkinConfig:
    global _active_skin
    skin_name = config.get("display", {}).get("skin", "default")
    _active_skin = load_skin(skin_name)
    return _active_skin


def load_skin(name: str) -> SkinConfig:
    skin_data = _BUILTIN_SKINS.get(name, _BUILTIN_SKINS["default"])
    return SkinConfig(**skin_data)


def get_active_skin() -> Optional[SkinConfig]:
    return _active_skin


def set_active_skin(name: str) -> Optional[SkinConfig]:
    global _active_skin
    _active_skin = load_skin(name)
    return _active_skin
