"""HTTP adapter for OpenAI-compatible local and remote endpoints."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Iterator

from .base import ProviderAdapter, ProviderAuthenticationError, ProviderConfigurationError, ProviderError, ProviderRequestError, ProviderUnavailable


class OpenAICompatibleAdapter(ProviderAdapter):
    provider_type = "openai_compatible"
    def __init__(self, model: dict[str, Any], *, provider_type: str | None = None, offline: bool = False):
        super().__init__(model)
        self.provider_type = provider_type or str(model.get("provider") or self.provider_type)
        self.offline = offline
        self.base_url = str(model.get("base_url", "")).rstrip("/")
        self.api_key = str(model.get("api_key", ""))
        self.timeout = float(model.get("timeout", 120))
    def _url(self, path: str) -> str:
        base = self.base_url.rstrip("/")
        if path.startswith("/v1/") and base.endswith("/v1"): return base + path[3:]
        return base + path
    def _request(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.base_url: raise ProviderConfigurationError("provider base_url is not configured")
        headers = {"Accept": "application/json"}
        if payload is not None: headers["Content-Type"] = "application/json"
        if self.api_key: headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(self._url(path), data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response: return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError("provider authentication failed", status=exc.code) from None
            if exc.code == 404: raise ProviderRequestError("provider endpoint was not found", status=exc.code) from None
            raise ProviderRequestError(f"provider returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError): raise ProviderUnavailable("provider is unavailable") from None
        except (json.JSONDecodeError, UnicodeDecodeError): raise ProviderRequestError("provider returned invalid JSON") from None
    def list_models(self) -> list[str]:
        data = self._request("/v1/models")
        values = data.get("data") or data.get("models") or []
        return [str(item.get("id") or item.get("name")) for item in values if isinstance(item, dict) and (item.get("id") or item.get("name"))]
    def health(self) -> bool:
        try: self._request("/health"); return True
        except ProviderError:
            try: self.list_models(); return True
            except ProviderError: return False
    def validate_model(self) -> bool:
        if not self.model_name: raise ProviderConfigurationError("provider model is not configured")
        names = self.list_models(); return not names or self.model_name in names
    def _stream_request(self, payload: dict[str, Any]) -> Iterator[str]:
        if not self.base_url: raise ProviderConfigurationError("provider base_url is not configured")
        headers = {"Accept": "text/event-stream", "Content-Type": "application/json"}
        if self.api_key: headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(self._url("/v1/chat/completions"), data=json.dumps(payload).encode(), headers=headers)
        try:
            response = urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError("provider authentication failed", status=exc.code) from None
            if exc.code == 404: raise ProviderRequestError("provider endpoint was not found", status=exc.code) from None
            raise ProviderRequestError(f"provider returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError): raise ProviderUnavailable("provider is unavailable") from None
        try:
            for raw in iter(response.readline, b""):
                line = raw.decode("utf-8", "replace").strip()
                if not line or not line.startswith("data:"): continue
                data = line[5:].strip()
                if data == "[DONE]": break
                try: event = json.loads(data)
                except json.JSONDecodeError: continue
                choices = event.get("choices") or []
                if not choices: continue
                delta = choices[0].get("delta") or {}
                text = delta.get("content")
                if text: yield str(text)
        finally:
            response.close()
    def stream_chat(self, prompt: str) -> Iterator[str]:
        payload = {"model": self.model_name, "messages": [{"role": "user", "content": prompt}], "temperature": self.model.get("temperature", 0.2), "max_tokens": self.model.get("max_tokens", 4096), "stream": True}
        yield from self._stream_request(payload)
    def chat(self, prompt: str) -> str:
        if not self.model_name: raise ProviderConfigurationError("provider model is not configured")
        payload = {"model": self.model_name, "messages": [{"role": "user", "content": prompt}], "temperature": self.model.get("temperature", 0.2), "max_tokens": self.model.get("max_tokens", 4096)}
        data = self._request("/v1/chat/completions", payload)
        choices = data.get("choices") or []
        if not choices: raise ProviderRequestError("provider returned no choices")
        content = (choices[0].get("message") or {}).get("content")
        if content is None: raise ProviderRequestError("provider returned an invalid message")
        return str(content)
