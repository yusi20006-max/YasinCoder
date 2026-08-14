#!/usr/bin/env python3
"""Portable first-run bootstrap for YasinCoder.

All machine-specific state is stored outside the repository under
~/.config/yasin-coder by default. No model is downloaded or assumed.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(os.getenv("YASIN_CONFIG_DIR", Path.home() / ".config" / "yasin-coder"))
CONFIG = APP_DIR / "config.json"
MODELS = APP_DIR / "models.json"


def check(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd)


def default_config() -> dict:
    return {
        "mode": "offline",
        "active_model": "",
        "project_path": str(Path.cwd()),
        "models_file": str(MODELS),
    }


def load(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return default


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def choose(prompt: str, options: list[str], default: int = 1) -> str:
    print(prompt)
    for i, option in enumerate(options, 1):
        print(f"  {i}) {option}")
    raw = input(f"Choice [{default}]: ").strip()
    try:
        idx = int(raw or default)
        return options[idx - 1]
    except (ValueError, IndexError):
        return options[default - 1]


def configure() -> None:
    cfg = load(CONFIG, default_config())
    models = load(MODELS, [])
    mode = choose("YasinCoder AI mode:", ["offline", "online"])
    cfg["mode"] = mode

    if mode == "offline":
        name = input("Local model name: ").strip()
        base = input("Local OpenAI-compatible URL [http://127.0.0.1:18080]: ").strip() or "http://127.0.0.1:18080"
        runtime = choose("Local runtime:", ["llama_cpp", "ollama", "openai_compatible"])
        model = input("Model identifier/path (owned by you, not Git): ").strip()
        entry = {"name": name or "local", "type": runtime, "base_url": base, "model": model, "offline": True, "fallbacks": []}
    else:
        name = input("Provider name [gemini]: ").strip() or "gemini"
        base = input("API base URL (leave blank for provider default): ").strip()
        model = input("Model name: ").strip()
        key = input("API key (leave blank to use environment/credential store): ").strip()
        runtime = "openai_compatible" if base else "gemini"
        entry = {"name": name, "type": runtime, "base_url": base, "model": model, "offline": False, "fallbacks": []}
        if key:
            print("API key entered; storing only in the external config is disabled by default. Use an environment variable instead.")
            print("Set YASIN_API_KEY in your shell/secret store and rerun configuration.")

    models = [m for m in models if m.get("name") != entry["name"]]
    models.append(entry)
    cfg["active_model"] = entry["name"]
    save(MODELS, models)
    save(CONFIG, cfg)
    print(f"Configuration saved outside Git: {APP_DIR}")


def doctor() -> int:
    print("YasinCoder environment check")
    checks = {"python3": check("python3"), "git": check("git")}
    for name, ok in checks.items():
        print(f"  {'OK' if ok else 'MISSING'}: {name}")
    cfg = load(CONFIG, None)
    print(f"  CONFIG: {'OK' if cfg else 'NOT CONFIGURED'} ({CONFIG})")
    models = load(MODELS, None)
    print(f"  MODELS: {'OK' if models is not None else 'NOT CONFIGURED'} ({MODELS})")
    return 0 if all(checks.values()) else 1


def reset() -> None:
    if not APP_DIR.exists():
        print("Nothing to reset.")
        return
    answer = input(f"Remove external YasinCoder configuration at {APP_DIR}? [y/N]: ").strip().lower()
    if answer == "y":
        shutil.rmtree(APP_DIR)
        print("External configuration removed. Repository files were not changed.")
    else:
        print("Reset cancelled.")


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "configure"
    if command == "configure":
        configure()
        return 0
    if command == "doctor":
        return doctor()
    if command == "reset":
        reset()
        return 0
    print("Usage: bootstrap.py [configure|doctor|reset]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
