"""Portable model registry and runtime discovery.

Machine-specific model definitions live outside the repository. Discovery never
assumes a developer model name; local runtimes advertise their own models.
"""
from __future__ import annotations

import json
import os
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
        model = dict(model)
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

    @staticmethod
    def _json(base: str, path: str) -> dict[str, Any] | None:
        try:
            with urllib.request.urlopen(base.rstrip("/") + path, timeout=2) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            return None

    def _discover_openai_models(self, base: str) -> list[str]:
        data = self._json(base, "/v1/models") or {}
        values = data.get("data") or data.get("models") or []
        names = []
        for item in values:
            if isinstance(item, dict) and item.get("id"):
                names.append(str(item["id"]))
            elif isinstance(item, dict) and item.get("name"):
                names.append(str(item["name"]))
        return names

    def discover(self) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []
        env_url = os.getenv("YASIN_BASE_URL", "").strip()
        env_model = os.getenv("YASIN_MODEL_NAME", "").strip()
        if env_url:
            found.append({"name": env_model or "configured-endpoint", "type": "openai_compatible", "base_url": env_url, "model": env_model})

        for base, kind in (("http://127.0.0.1:18080", "llama_cpp"), ("http://127.0.0.1:11434", "ollama")):
            names = self._discover_openai_models(base) if kind == "llama_cpp" else []
            if kind == "ollama":
                data = self._json(base, "/api/tags") or {}
                names = [str(x.get("name")) for x in data.get("models", []) if isinstance(x, dict) and x.get("name")]
            for model_name in names:
                found.append({"name": f"{kind}:{model_name}", "type": kind, "base_url": base, "model": model_name, "offline": True})
        return found

    def ensure_discovered(self) -> list[dict[str, Any]]:
        discovered = [self.upsert(model) for model in self.discover()]
        if not self.default() and discovered:
            self.select(discovered[0]["name"])
        return discovered
