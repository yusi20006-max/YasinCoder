"""Portable compatibility configuration.

Keep secrets and machine-specific values outside the repository. Environment
variables override the safe defaults so a clean clone does not depend on the
developer's filesystem or model.
"""

import os

PROJECT_PATH = os.getenv("YASIN_PROJECT_PATH", os.getcwd())
API_KEY = os.getenv("YASIN_API_KEY", "")
BASE_URL = os.getenv("YASIN_BASE_URL", "")
MODEL = os.getenv("YASIN_MODEL", "auto")
TEMPERATURE = float(os.getenv("YASIN_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("YASIN_MAX_TOKENS", "4096"))

# Cloudflare Workers AI compatibility settings.
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
CF_MODEL = os.getenv("CF_MODEL", "@cf/meta/llama-3-8b-instruct")
