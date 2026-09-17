"""First-run Gemini BYOK setup using Google's OpenAI-compatible endpoint."""
from __future__ import annotations

import json
import os
import stat
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from models.manager import ModelManager

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
PREFERRED_MODELS = (
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash",
)


class GeminiSetupError(RuntimeError):
    """Raised when Gemini setup cannot be completed safely."""


def credential_path() -> Path:
    configured = os.getenv("YASIN_GEMINI_CREDENTIAL_FILE", "").strip()
    if configured:
        return Path(configured).expanduser()
    config_home = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "yasin-coder" / "gemini.key"


def _request(path: str, api_key: str, *, timeout: float = 10) -> dict[str, Any]:
    request = urllib.request.Request(
        GEMINI_BASE_URL.rstrip("/") + path,
        headers={
            "Accept": "application/json",
            "Authorization": "Bearer " + api_key,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise GeminiSetupError("Gemini API key was rejected") from None
        raise GeminiSetupError(f"Gemini API returned HTTP {exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise GeminiSetupError("could not reach the Gemini API") from None
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise GeminiSetupError("Gemini returned invalid JSON") from None


def discover_models(api_key: str) -> list[str]:
    key = str(api_key).strip()
    if not key:
        raise GeminiSetupError("Gemini API key is required")
    data = _request("/models", key)
    models: list[str] = []
    for item in data.get("data", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("id") or item.get("name") or "").strip()
        if name.startswith("models/"):
            name = name[7:]
        if name.startswith("gemini-"):
            models.append(name)
    if not models:
        raise GeminiSetupError("Gemini API returned no compatible Gemini models")
    return sorted(set(models))


def choose_model(models: list[str]) -> str:
    available = {str(model).strip() for model in models if str(model).strip()}
    for preferred in PREFERRED_MODELS:
        if preferred in available:
            return preferred
    flash = sorted(model for model in available if "flash" in model.lower())
    return flash[0] if flash else sorted(available)[0]


def save_credential(api_key: str, path: Path | None = None) -> Path:
    key = str(api_key).strip()
    if not key:
        raise GeminiSetupError("Gemini API key is required")
    target = path or credential_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(target, flags, 0o600)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            handle.write(key + "\n")
    finally:
        if fd != -1:
            os.close(fd)
    return target


def setup_gemini(api_key: str, manager: ModelManager | None = None) -> dict[str, Any]:
    """Validate key, persist it separately, register Gemini, and select it as default."""
    manager = manager or ModelManager()
    models = discover_models(api_key)
    selected = choose_model(models)
    credential = save_credential(api_key)
    credential_env = "YASIN_GEMINI_CREDENTIAL_FILE"
    model = {
        "name": "gemini",
        "type": "gemini",
        "base_url": GEMINI_BASE_URL,
        "model": selected,
        "aliases": ["google", "gemini-default"],
        "api_key_file_env": credential_env,
        "timeout": 120,
        "temperature": 0.2,
        "max_tokens": 4096,
    }
    manager.upsert(model)
    manager.select("gemini")
    return {"name": "gemini", "model": selected, "credential_file": str(credential)}


def interactive_setup(manager: ModelManager | None = None) -> dict[str, Any]:
    import getpass

    print("Gemini first-run setup")
    print("Get your API key from Google AI Studio.")
    api_key = getpass.getpass("Gemini API key: ")
    result = setup_gemini(api_key, manager=manager)
    print(f"Gemini configured: {result['model']}")
    print("The API key is stored in a user-only credential file; it is not printed or placed in the model registry.")
    return result
