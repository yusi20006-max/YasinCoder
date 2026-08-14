"""llama.cpp server adapter using its OpenAI-compatible API."""
from __future__ import annotations

from typing import Any

from .http_compatible import OpenAICompatibleAdapter


class LlamaCppAdapter(OpenAICompatibleAdapter):
    provider_type = "llama_cpp"
    offline = True

    def __init__(self, model: dict[str, Any]):
        super().__init__(model, provider_type="llama_cpp", offline=True)
