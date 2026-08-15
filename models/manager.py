"""Portable model registry, validation, secret references and discovery."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "yasin-coder"
DEFAULT_MODELS_FILE = DEFAULT_CONFIG_DIR / "models.json"
SCHEMA_VERSION = 2
SECRET_KEYS = {"api_key", "api_token", "token", "password", "secret"}
SUPPORTED_TYPES = {
    "openai_compatible",
    "openai",
    "custom",
    "ollama",
    "llama_cpp",
    "cloudflare",
    "gemini",
}


def _path() -> Path:
    return Path(os.getenv("YASIN_MODELS_FILE", str(DEFAULT_MODELS_FILE))).expanduser()


def _default_data() -> dict[str, Any]:
    return {"version": SCHEMA_VERSION, "default": "", "models": []}


class ModelValidationError(ValueError):
    """Raised when a model definition is invalid or unsafe to persist."""


class ModelManager:
    """User-owned registry. Secrets are referenced by environment variable only."""

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path).expanduser() if path else _path()
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return _default_data()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ModelValidationError(f"cannot read model registry {self.path}: {exc}") from exc
        if not isinstance(data, dict) or not isinstance(data.get("models"), list):
            raise ModelValidationError("model registry must contain an object with a models list")
        data.setdefault("version", SCHEMA_VERSION)
        data.setdefault("default", "")
        for model in data["models"]:
            self.validate(model)
        return data

    @staticmethod
    def validate(model: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(model, dict):
            raise ModelValidationError("model definition must be an object")
        name = str(model.get("name", "")).strip()
        kind = str(model.get("type", "")).strip().lower()
        if not name:
            raise ModelValidationError("model requires a non-empty name")
        if not kind or kind not in SUPPORTED_TYPES:
            raise ModelValidationError(f"unsupported provider type: {kind or '<empty>'}")
        for key in SECRET_KEYS:
            if key in model and model[key]:
                raise ModelValidationError(f"secret value '{key}' must not be stored; use an *_ENV reference")
        aliases = model.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
            model["aliases"] = aliases
        if not isinstance(aliases, list) or not all(isinstance(x, str) and x.strip() for x in aliases):
            raise ModelValidationError("aliases must be a list of non-empty strings")
        if "base_url" in model and model["base_url"] and not isinstance(model["base_url"], str):
            raise ModelValidationError("base_url must be a string")
        for key in ("timeout", "temperature"):
            if key in model:
                try:
                    value = float(model[key])
                except (TypeError, ValueError) as exc:
                    raise ModelValidationError(f"{key} must be numeric") from exc
                if value < 0:
                    raise ModelValidationError(f"{key} must be >= 0")
        if "max_tokens" in model:
            try:
                if int(model["max_tokens"]) <= 0:
                    raise ValueError
            except (TypeError, ValueError) as exc:
                raise ModelValidationError("max_tokens must be a positive integer") from exc
        for key, value in model.items():
            if key.endswith("_env") and value and (not isinstance(value, str) or not value.strip()):
                raise ModelValidationError(f"{key} must name an environment variable")
        return model

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def list(self) -> list[dict[str, Any]]:
        return sorted((dict(m) for m in self.data["models"]), key=lambda m: str(m.get("name", "")).lower())

    def get(self, name: str) -> dict[str, Any] | None:
        needle = str(name).strip().lower()
        for model in self.data["models"]:
            if str(model.get("name", "")).lower() == needle:
                return dict(model)
            if needle in {str(alias).strip().lower() for alias in model.get("aliases", [])}:
                return dict(model)
        return None

    def upsert(self, model: dict[str, Any]) -> dict[str, Any]:
        model = dict(model)
        self.validate(model)
        models = self.data["models"]
        for i, current in enumerate(models):
            if str(current.get("name", "")).lower() == str(model["name"]).lower():
                models[i] = {**current, **model}
                self.save()
                return dict(models[i])
        models.append(model)
        self.save()
        return dict(model)

    def remove(self, name: str) -> bool:
        model = self.get(name)
        if not model:
            return False
        target = model["name"]
        before = len(self.data["models"])
        self.data["models"] = [m for m in self.data["models"] if m.get("name") != target]
        if self.data.get("default") == target:
            self.data["default"] = ""
        changed = len(self.data["models"]) != before
        if changed:
            self.save()
        return changed

    def select(self, name: str) -> dict[str, Any]:
        model = self.get(name)
        if not model:
            raise KeyError(f"unknown model: {name}")
        self.data["default"] = model["name"]
        self.save()
        return model

    def default(self) -> dict[str, Any] | None:
        requested = os.getenv("YASIN_MODEL", "").strip()
        if requested and requested.lower() != "auto":
            return self.get(requested)
        configured = str(self.data.get("default", "")).strip()
        if configured:
            return self.get(configured)
        models = self.list()
        return models[0] if models else None

    @staticmethod
    def resolve_secrets(model: dict[str, Any]) -> dict[str, Any]:
        """Return a runtime copy with environment-backed credentials resolved."""
        resolved = dict(model)
        for key, env_name in list(model.items()):
            if not key.endswith("_env") or not env_name:
                continue
            target = key[:-4]
            value = os.getenv(str(env_name), "")
            if value:
                resolved[target] = value
        return resolved

    @staticmethod
    def _json(base: str, path: str, *, timeout: float = 3) -> dict[str, Any] | None:
        try:
            request = urllib.request.Request(base.rstrip("/") + path, headers={"Accept": "application/json"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, urllib.error.URLError, urllib.error.HTTPError):
            return None

    @staticmethod
    def _openai_base(base: str) -> str:
        return base.rstrip("/")[:-3] if base.rstrip("/").endswith("/v1") else base.rstrip("/")

    def _discover_openai_models(self, base: str) -> list[str]:
        data = self._json(self._openai_base(base), "/v1/models") or {}
        values = data.get("data") or data.get("models") or []
        return [
            str(x.get("id") or x.get("name"))
            for x in values
            if isinstance(x, dict) and (x.get("id") or x.get("name"))
        ]

    def _discover_ollama_models(self, base: str) -> list[str]:
        data = self._json(base, "/api/tags") or {}
        return [
            str(x.get("name"))
            for x in data.get("models", [])
            if isinstance(x, dict) and x.get("name")
        ]

    def discover(self) -> list[dict[str, Any]]:
        """Discover configured and locally reachable providers without persisting secrets."""
        found: list[dict[str, Any]] = []

        env_url = os.getenv("YASIN_BASE_URL", "").strip()
        env_model = os.getenv("YASIN_MODEL_NAME", "").strip()
        if env_url:
            names = self._discover_openai_models(env_url)
            if env_model and env_model not in names:
                names.insert(0, env_model)
            if not names:
                names = ["configured-endpoint"] if env_model else []
            for model_name in names:
                found.append({
                    "name": model_name if len(names) == 1 else f"openai:{model_name}",
                    "type": "openai_compatible",
                    "base_url": env_url,
                    "model": model_name if model_name != "configured-endpoint" else env_model,
                    "api_key_env": "YASIN_API_KEY" if os.getenv("YASIN_API_KEY") else "",
                    "timeout": float(os.getenv("YASIN_TIMEOUT", "120")),
                    "temperature": float(os.getenv("YASIN_TEMPERATURE", "0.2")),
                    "max_tokens": int(os.getenv("YASIN_MAX_TOKENS", "4096")),
                })

        google_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if google_key:
            gemini_base = os.getenv(
                "GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta/openai",
            ).strip()
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
            names = self._discover_openai_models(gemini_base)
            if gemini_model and gemini_model not in names:
                names.insert(0, gemini_model)
            for model_name in names:
                found.append({
                    "name": f"gemini:{model_name}",
                    "type": "gemini",
                    "base_url": gemini_base,
                    "model": model_name,
                    "api_key_env": "GEMINI_API_KEY" if os.getenv("GEMINI_API_KEY") else "GOOGLE_API_KEY",
                })

        cf_id = os.getenv("CF_ACCOUNT_ID", "").strip()
        cf_token = os.getenv("CF_API_TOKEN", "").strip()
        cf_model = os.getenv("CF_MODEL", "").strip()
        if cf_id and cf_model:
            found.append({
                "name": "cloudflare",
                "type": "cloudflare",
                "model": cf_model,
                "account_id_env": "CF_ACCOUNT_ID",
                "api_token_env": "CF_API_TOKEN" if cf_token else "",
            })

        local_endpoints = (
            ("http://127.0.0.1:18080", "llama_cpp", self._discover_openai_models),
            ("http://127.0.0.1:11434", "ollama", self._discover_ollama_models),
        )
        for base, kind, discoverer in local_endpoints:
            for model_name in discoverer(base):
                found.append({
                    "name": f"{kind}:{model_name}",
                    "type": kind,
                    "base_url": base,
                    "model": model_name,
                    "offline": True,
                })
        return found

    def ensure_discovered(self) -> list[dict[str, Any]]:
        discovered: list[dict[str, Any]] = []
        for model in self.discover():
            try:
                discovered.append(self.upsert(model))
            except ModelValidationError:
                continue
        if not self.default() and discovered:
            self.select(sorted(discovered, key=lambda x: x["name"].lower())[0]["name"])
        return discovered

    def validate_all(self) -> list[str]:
        errors = []
        names: set[str] = set()
        aliases: dict[str, str] = {}
        for model in self.data["models"]:
            try:
                self.validate(model)
            except ModelValidationError as exc:
                errors.append(str(exc))
                continue
            name = str(model["name"]).lower()
            if name in names:
                errors.append(f"duplicate model name: {model['name']}")
            names.add(name)
            for alias in model.get("aliases", []):
                key = alias.lower()
                if key in names or (key in aliases and aliases[key] != model["name"]):
                    errors.append(f"duplicate model alias: {alias}")
                aliases[key] = model["name"]
        return errors
