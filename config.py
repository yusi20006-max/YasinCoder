PROJECT_PATH="/data/data/com.termux/files/home/YasinCoder"

API_KEY=""

BASE_URL=""

MODEL="auto"

TEMPERATURE=0.2

MAX_TOKENS=4096

# Cloudflare Workers AI (used by providers/cloudflare.py).
# Leave CF_ACCOUNT_ID / CF_API_TOKEN empty until you have a Cloudflare
# account with Workers AI enabled; the app now falls back gracefully
# instead of crashing on startup when these are unset.
CF_ACCOUNT_ID=""

CF_API_TOKEN=""

CF_MODEL="@cf/meta/llama-3-8b-instruct"
