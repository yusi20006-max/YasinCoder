"""Portable model registry and runtime discovery.

Machine-specific model definitions live outside the repository. The registry
uses XDG_CONFIG_HOME (or ~/.config) and can be overridden with
YASIN_MODELS_FILE for tests or custom deployments.
"""
from __future__ import annotations

import json
import os
import shutil
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "yasin-coder"
DEFAULT_MODELS_FILE = DEFAULT_CONFIG_DIR / "models.json"


def _path() -> Path:
    return Path(os.getenv("YASIN_MODELS_FILE", str(DEFAULT_MODELS_FILE))).expanduser()


class ModelManager:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path).expanduser() if path else _path()
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "default": "", "models": []}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("models"), list):
                return data
        except (OSError, ValueError):
            pass
        return {"version": 1, "default": "", "models": []}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def list(self) -> list[dict[str, Any]]:
        return list(self.data["models"])

    def get(self, name: str) -> dict[str, Any] | None:
        return next((m for m in self.data["models"] if m.get("name") == name), None)

    def upsert(self, model: dict[str, Any]) -> dict[str, Any]:
        if not model.get("name") or not model.get("type"):
            raise ValueError("model requires name and type")
        models = self.data["models"]
        for i, current in enumerate(models):
            if current.get("name") == model["name"]:
                models[i] = {**current, **model}
                self.save()
                return models[i]
        models.append(model)
        self.save()
        return model

    def remove(self, name: str) -> bool:
        before = len(self.data["models"])
        self.data["models"] = [m for m in self.data["models"] if m.get("name") != name]
        if self.data.get("default") == name:
            self.data["default"] = ""
        changed = len(self.data["models"]) != before
        if changed:
            self.save()
        return changed

    def select(self, name: str) -> dict[str, Any]:
        model = self.get(name)
        if not model:
            raise KeyError(name)
        self.data["default"] = name
        self.save()
        return model

    def default(self) -> dict[str, Any] | None:
        name = os.getenv("YASIN_MODEL", "").strip() or self.data.get("default", "")
        return self.get(name) if name else (self.data["models"][0] if self.data["models"] else None)

    def discover(self) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        env_url = os.getenv("YASIN_BASE_URL", "").strip()
        env_model = os.getenv("YASIN_MODEL_NAME", "").strip()
        if env_url:
            found.append({"name": env_model or "configured-endpoint", "type": "openai_compatible", "base_url": env_url, "model": env_model})
        probes = [
            ("llama-cpp", "http://127.0.0.1:18080", "qwen3-local"),
            ("ollama", "http://127.0.0.1:11434", ""),
        ]
        for name, base, model in probes:
            if self._healthy(base):
                found.append({"name": name, "type": "ollama" if name == "ollama" else "llama_cpp", "base_url": base, "model": model})
        return found

    @staticmethod
    def _healthy(base: str) -> bool:
        for endpoint in ("/health", "/api/tags", "/v1/models"):
            try:
                with urllib.request.urlopen(base.rstrip("/") + endpoint, timeout=1.5) as response:
                    if 200 <= response.status < 300:
                        return True
            except Exception:
                continue
        return False

    def ensure_discovered(self) -> list[dict[str, Any]]:
        discovered = []
        for model in self.discover():
            discovered.append(self.upsert(model))
        if not self.default() and discovered:
            self.select(discovered[0]["name"])
        return discovered
