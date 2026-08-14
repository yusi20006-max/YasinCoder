import os

PROJECT_PATH = os.getenv(
    "YASIN_PROJECT_PATH",
    "/data/data/com.termux/files/home/YasinCoder",
)

API_KEY = os.getenv("YASIN_API_KEY", "")
BASE_URL = os.getenv("YASIN_BASE_URL", "")
MODEL = os.getenv("YASIN_MODEL", "auto")
TEMPERATURE = float(os.getenv("YASIN_TEMPERATURE", "0.2"))
MAX_TOKENS = int(os.getenv("YASIN_MAX_TOKENS", "4096"))

# Unified local/remote gateway used by YasinCoder.
# The gateway owns local Qwen/llama.cpp lifecycle and routing.
GATEWAY_URL = os.getenv("YASIN_GATEWAY_URL", "http://127.0.0.1:18765")
GATEWAY_TIMEOUT = float(os.getenv("YASIN_GATEWAY_TIMEOUT", "120"))

# Cloudflare Workers AI.
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CF_API_TOKEN", "")
CF_MODEL = os.getenv("CF_MODEL", "@cf/meta/llama-3-8b-instruct")
