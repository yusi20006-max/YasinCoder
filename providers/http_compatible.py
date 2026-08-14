"""HTTP adapter for OpenAI-compatible local and remote endpoints."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from .base import ProviderAdapter, ProviderAuthenticationError, ProviderConfigurationError, ProviderRequestError, ProviderUnavailable


class OpenAICompatibleAdapter(ProviderAdapter):
    provider_type = "openai_compatible"

    def __init__(self, model: dict[str, Any], *, provider_type: str | None = None, offline: bool = False):
        super().__init__(model)
        self.provider_type = provider_type or str(model.get("provider") or self.provider_type)
        self.offline = offline
        self.base_url = str(model.get("base_url", "")).rstrip("/")
        self.api_key = str(model.get("api_key", ""))
        self.timeout = float(model.get("timeout", 120))

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.base_url:
            raise ProviderConfigurationError("provider base_url is not configured")
        headers = {"Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if self.api_key:
            headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(self.base_url + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise ProviderAuthenticationError("provider authentication failed", status=exc.code) from None
            raise ProviderRequestError(f"provider returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError):
            raise ProviderUnavailable("provider is unavailable") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ProviderRequestError("provider returned invalid JSON") from None

    def health(self) -> bool:
        for path in ("/health", "/v1/models", "/api/tags"):
            try:
                self._request(path)
                return True
            except ProviderError:
                continue
        return False

    def chat(self, prompt: str) -> str:
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.model.get("temperature", 0.2),
            "max_tokens": self.model.get("max_tokens", 4096),
        }
        data = self._request("/v1/chat/completions", payload)
        choices = data.get("choices") or []
        if not choices:
            raise ProviderRequestError("provider returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content", "")
        return str(content)
