"""Ollama-native provider adapter."""
from __future__ import annotations
import json
import urllib.error
import urllib.request
from typing import Any, Iterator
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
        if not self.base_url: raise ProviderConfigurationError("Ollama base_url is not configured")
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key: headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(self.base_url + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response: return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError("Ollama authentication failed", status=exc.code) from None
            raise ProviderRequestError(f"Ollama returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError): raise ProviderUnavailable("Ollama is unavailable") from None
        except (json.JSONDecodeError, UnicodeDecodeError): raise ProviderRequestError("Ollama returned invalid JSON") from None
    def health(self) -> bool:
        try: self._request("/api/tags"); return True
        except ProviderError: return False
    def list_models(self) -> list[str]:
        data = self._request("/api/tags")
        return [str(x.get("name")) for x in (data.get("models") or []) if isinstance(x, dict) and x.get("name")]
    def validate_model(self) -> bool:
        names = self.list_models(); return not names or self.model_name in names
    def stream_chat(self, prompt: str) -> Iterator[str]:
        if not self.model_name: raise ProviderConfigurationError("Ollama model is not configured")
        payload = {"model": self.model_name, "prompt": prompt, "stream": True}
        headers = {"Accept": "application/x-ndjson", "Content-Type": "application/json"}
        if self.api_key: headers["Authorization"] = "Bearer " + self.api_key
        request = urllib.request.Request(self.base_url + "/api/generate", data=json.dumps(payload).encode(), headers=headers)
        try: response = urllib.request.urlopen(request, timeout=self.timeout)
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403): raise ProviderAuthenticationError("Ollama authentication failed", status=exc.code) from None
            raise ProviderRequestError(f"Ollama returned HTTP {exc.code}", status=exc.code) from None
        except (urllib.error.URLError, TimeoutError, OSError): raise ProviderUnavailable("Ollama is unavailable") from None
        try:
            for raw in iter(response.readline, b""):
                line = raw.decode("utf-8", "replace").strip()
                if not line: continue
                try: data = json.loads(line)
                except json.JSONDecodeError: continue
                text = data.get("response")
                if text: yield str(text)
                if data.get("done"): break
        finally: response.close()
    def chat(self, prompt: str) -> str:
        data = self._request("/api/generate", {"model": self.model_name, "prompt": prompt, "stream": False})
        return str(data.get("response", ""))
