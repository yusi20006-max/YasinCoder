PROJECT_PATH="/data/data/com.termux/files/home/YasinPress-AI-Engine"

API_KEY=""

BASE_URL=""

MODEL="auto"

TEMPERATURE=0.2

MAX_TOKENS=4096

from pathlib import Path

BASE_DIR = Path(__file__).parent

CF_TOKEN_FILE = BASE_DIR / "cf_token.txt"
CF_ACCOUNT_FILE = BASE_DIR / "cf_account.txt"

def load_secret(path):
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""

CF_TOKEN = load_secret(CF_TOKEN_FILE)
CF_ACCOUNT_ID = load_secret(CF_ACCOUNT_FILE)

CF_MODEL = "@cf/meta/llama-3.1-8b-instruct"

