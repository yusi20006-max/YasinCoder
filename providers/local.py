"""Generic local AI provider.

Supports OpenAI-compatible local servers (llama.cpp and similar) and Ollama.
All runtime/model details are user configuration; no model is bundled here.
"""

import json
import os
import urllib.error
import urllib.request

from providers.base import BaseProvider


class LocalProvider(BaseProvider):
    name = "local"

    def __init__(self, runtime=None, base_url=None, model=None, timeout=None):
        self.runtime = (runtime or os.getenv("YASIN_LOCAL_RUNTIME", "openai")).lower()
        self.base_url = (base_url or os.getenv("YASIN_LOCAL_BASE_URL", "http://127.0.0.1:11434")).rstrip("/")
        self.model = model or os.getenv("YASIN_LOCAL_MODEL", "local-model")
        self.timeout = float(timeout or os.getenv("YASIN_LOCAL_TIMEOUT", "120"))

    def capabilities(self):
        return {"chat": True, "streaming": False, "runtime": self.runtime, "model": self.model}

    def _request(self, path, payload=None):
        url = self.base_url + path
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST" if payload is not None else "GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Local provider HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Local provider unavailable: {exc.reason}") from exc

    def health(self) -> bool:
        try:
            if self.runtime == "ollama":
                self._request("/api/tags")
            else:
                self._request("/v1/models")
            return True
        except Exception:
            return False

    def chat(self, prompt: str) -> str:
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be a non-empty string")

        if self.runtime == "ollama":
            result = self._request(
                "/api/chat",
                {"model": self.model, "messages": [{"role": "user", "content": prompt}], "stream": False},
            )
            return str(result.get("message", {}).get("content", ""))

        endpoint = "/v1/chat/completions" if not self.base_url.endswith("/v1") else "/chat/completions"
        result = self._request(
            endpoint,
            {"model": self.model, "messages": [{"role": "user", "content": prompt}]},
        )
        try:
            return str(result["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Invalid local provider response: {result}") from exc
