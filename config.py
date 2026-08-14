"""Portable configuration defaults.

Secrets and machine-specific settings should come from the environment or
user-owned runtime configuration, never from the repository.
"""

import os
from pathlib import Path

PROJECT_PATH = os.getenv("YASIN_PROJECT_PATH", str(Path.cwd()))
API_KEY = os.getenv("YASIN_API_KEY", "")
BASE_URL = os.getenv("YASIN_BASE_URL", "")
MODEL = os.getenv("YASIN_MODEL", "auto")
TEMPERATURE = float(os.getenv("YASIN_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("YASIN_MAX_TOKENS", "4096"))

# Cloudflare remains supported as an existing remote provider, but credentials
# are user-owned. Files are resolved from the optional YASIN_CONFIG_DIR.
CONFIG_DIR = Path(os.getenv("YASIN_CONFIG_DIR", Path.home() / ".yasin-coder"))
CF_TOKEN_FILE = CONFIG_DIR / "cf_token.txt"
CF_ACCOUNT_FILE = CONFIG_DIR / "cf_account.txt"


def load_secret(path):
    try:
        return path.read_text(encoding="utf-8").strip()
    except (FileNotFoundError, OSError):
        return ""


CF_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", load_secret(CF_TOKEN_FILE))
CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", load_secret(CF_ACCOUNT_FILE))
CF_MODEL = os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.1-8b-instruct")
