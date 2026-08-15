"""Environment and model configuration diagnostics."""
from __future__ import annotations

import os
import sys

from models.manager import ModelManager, ModelValidationError


def run() -> int:
    print("=" * 60)
    print("YasinCoder Doctor")
    print("=" * 60)
    print("Python :", sys.version.split()[0])

    folders = ["commands", "core", "providers", "models"]
    for folder in folders:
        print("[ OK ]" if os.path.isdir(folder) else "[FAIL]", folder)

    files = ["main.py", "router.py", "agent.py", "project.py", "config.py", "ai_client.py"]
    for file in files:
        print("[ OK ]" if os.path.isfile(file) else "[FAIL]", file)

    try:
        manager = ModelManager()
        errors = manager.validate_all()
        default = manager.default()
        print("Models :", len(manager.list()))
        print("Config :", manager.path)
        print("Default:", default.get("name") if default else "NOT CONFIGURED")
        if errors:
            print("[FAIL] Model validation:")
            for error in errors:
                print("  -", error)
            return 1
        if not default:
            print("[INFO] No model configured. Set YASIN_BASE_URL/YASIN_MODEL_NAME or add a model to the user registry.")
        else:
            print("[ OK ] Model registry")
        return 0
    except ModelValidationError as exc:
        print("[FAIL] Model registry:", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(run())
