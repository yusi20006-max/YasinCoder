"""OpenAI-compatible local runtime adapter for llama.cpp, Ollama, and peers."""
from __future__ import annotations

import json
import urllib.request


class ModelEndpoint:
    def __init__(self, model: dict):
        self.model = model
        self.base_url = str(model.get("base_url", "")).rstrip("/")

    def health(self) -> bool:
        candidates = ["/health", "/api/tags", "/v1/models"]
        for path in candidates:
            try:
                with urllib.request.urlopen(self.base_url + path, timeout=3) as response:
                    if 200 <= response.status < 300:
                        return True
            except Exception:
                continue
        return False

    def chat(self, prompt: str) -> str:
        kind = self.model.get("type")
        if kind == "ollama":
            payload = {"model": self.model.get("model", ""), "prompt": prompt, "stream": False}
            url = self.base_url + "/api/generate"
        else:
            payload = {
                "model": self.model.get("model") or self.model.get("name", "local"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.model.get("temperature", 0.2),
                "max_tokens": self.model.get("max_tokens", 4096),
            }
            url = self.base_url + "/v1/chat/completions"
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=float(self.model.get("timeout", 120))) as response:
            data = json.loads(response.read().decode())
        if kind == "ollama":
            return str(data.get("response", ""))
        choices = data.get("choices", [])
        return str(choices[0].get("message", {}).get("content", "")) if choices else str(data)
