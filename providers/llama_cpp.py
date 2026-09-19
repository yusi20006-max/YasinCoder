"""llama.cpp server adapter using its OpenAI-compatible API."""
from __future__ import annotations

import os
from typing import Any

from .http_compatible import OpenAICompatibleAdapter


class LlamaCppAdapter(OpenAICompatibleAdapter):
    provider_type = "llama_cpp"
    offline = True
    DEFAULT_MAX_TOKENS = 512
    MAX_TOKENS_ENV = "YASIN_LLAMA_MAX_TOKENS"

    def __init__(self, model: dict[str, Any]):
        super().__init__(model, provider_type="llama_cpp", offline=True)
        configured = os.getenv(self.MAX_TOKENS_ENV)
        if configured:
            self.model["max_tokens"] = int(configured)
        elif "max_tokens" not in self.model:
            self.model["max_tokens"] = self.DEFAULT_MAX_TOKENS
