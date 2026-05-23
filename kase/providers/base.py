"""Base provider interfaces and registry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ProviderProfile:
    name: str
    display_name: str
    api_mode: str = "chat_completions"
    base_url: str = ""
    env_key: str = ""
    models: List[str] = field(default_factory=list)
    context_length: int = 128000
    check_fn: Optional[Callable] = None


class BaseLLMProvider(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        ...

    @abstractmethod
    def chat_stream(self, messages: List[Dict], **kwargs):
        ...


class ProviderRegistry:
    def __init__(self):
        self._profiles: Dict[str, ProviderProfile] = {}

    def register_provider(self, profile: ProviderProfile) -> None:
        self._profiles[profile.name] = profile

    def get_provider(self, name: str) -> Optional[ProviderProfile]:
        return self._profiles.get(name)

    def list_providers(self) -> List[str]:
        return sorted(self._profiles.keys())

    def get_provider_by_model(self, model: str) -> Optional[ProviderProfile]:
        for profile in self._profiles.values():
            if model in profile.models:
                return profile
            for pm in profile.models:
                if pm.lower() in model.lower() or model.lower().startswith(pm.lower()):
                    return profile
        return None

    def is_provider_available(self, name: str) -> bool:
        profile = self._profiles.get(name)
        if not profile:
            return False
        if profile.check_fn:
            try:
                return bool(profile.check_fn())
            except Exception:
                return False
        return True

    def get_available_providers(self) -> List[str]:
        return [name for name in self._profiles if self.is_provider_available(name)]
