"""Ollama-native provider adapter."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderAdapter, ProviderAuthenticationError, ProviderConfigurationError, ProviderRequestError, ProviderUnavailable


class OllamaAdapter(ProviderAdapter):
    provider_type = "ollama"
    offline = True

    def __init__(self, model: dict[str, Any]):
        super().__init__(model)
        self.base_url = str(model.get("base_url", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = float(model.get("timeout", 120))
        self.api_key = str(model.get("api_key", ""))

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.base_url:
            raise ProviderConfigurationError("Ollama base_url is not configured")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(self.base_url + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderAuthenticationError("Ollama authentication failed", status=exc.code) from None
            raise ProviderRequestError(f"Ollama returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderUnavailable("Ollama is unavailable") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ProviderRequestError("Ollama returned invalid JSON") from None

    def health(self) -> bool:
        try:
            self._request("/api/tags")
            return True
        except Exception:
            return False

    def chat(self, prompt: str) -> str:
        data = self._request("/api/generate", {"model": self.model_name, "prompt": prompt, "stream": False})
        return str(data.get("response", ""))
