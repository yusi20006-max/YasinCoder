"""Construct adapters from portable model configuration."""
from __future__ import annotations

from typing import Any

from .base import ProviderConfigurationError, ProviderAdapter
from .http_compatible import OpenAICompatibleAdapter
from .llama_cpp import LlamaCppAdapter
from .ollama import OllamaAdapter


def create_adapter(model: dict[str, Any]) -> ProviderAdapter:
    kind = str(model.get("type", "")).strip().lower()
    if kind == "llama_cpp":
        return LlamaCppAdapter(model)
    if kind == "ollama":
        return OllamaAdapter(model)
    if kind in {"openai_compatible", "openai", "custom"}:
        return OpenAICompatibleAdapter(model)
    if kind == "cloudflare":
        from .cloudflare import CloudflareProvider
        return CloudflareProvider(model)
    raise ProviderConfigurationError(f"unsupported provider type: {kind or 'empty'}")
