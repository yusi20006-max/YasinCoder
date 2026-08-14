"""Provider-neutral adapter contract and normalized provider errors."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ProviderError(RuntimeError):
    kind = "provider_error"

    def __init__(self, message: str, *, status: int | None = None):
        super().__init__(message)
        self.status = status


class ProviderUnavailable(ProviderError):
    kind = "unavailable"


class ProviderAuthenticationError(ProviderError):
    kind = "authentication"


class ProviderConfigurationError(ProviderError):
    kind = "configuration"


class ProviderRequestError(ProviderError):
    kind = "request"


@dataclass(frozen=True)
class ModelInfo:
    name: str
    provider: str
    model: str
    offline: bool
    capabilities: tuple[str, ...] = ("chat",)

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "provider": self.provider, "model": self.model, "offline": self.offline, "capabilities": list(self.capabilities)}


class ProviderAdapter(ABC):
    """Stable interface consumed by gateway and routing layers."""
    provider_type = "unknown"
    offline = False

    def __init__(self, model: dict[str, Any]):
        self.model = model

    @property
    def name(self) -> str:
        return str(self.model.get("name") or self.model.get("model") or self.provider_type)

    @property
    def model_name(self) -> str:
        return str(self.model.get("model") or self.name)

    @abstractmethod
    def health(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def chat(self, prompt: str) -> str:
        raise NotImplementedError

    def info(self) -> ModelInfo:
        return ModelInfo(self.name, self.provider_type, self.model_name, self.offline)
