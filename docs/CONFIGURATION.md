# YasinCoder Configuration Contract

## Environment variables

| Variable | Purpose | Example |
|---|---|---|
| `YASIN_PROJECT_PATH` | Workspace/project root | `/home/user/project` |
| `YASIN_MODEL` | Provider/model selection | `auto` |
| `YASIN_BASE_URL` | OpenAI-compatible/custom endpoint | `http://127.0.0.1:18080/v1` |
| `YASIN_API_KEY` | Provider credential | user supplied |
| `YASIN_TEMPERATURE` | Generation temperature | `0.2` |
| `YASIN_MAX_TOKENS` | Output token budget | `4096` |
| `CF_ACCOUNT_ID` | Cloudflare account | user supplied |
| `CF_API_TOKEN` | Cloudflare credential | user supplied |
| `CF_MODEL` | Cloudflare model | provider-specific |

## Local AI

YasinCoder does not ship a model. Users may point it at their own llama.cpp,
Ollama, or another compatible local server. The model path, endpoint, alias,
context size and runtime flags belong to the user's machine configuration.

For example, a user can configure a local OpenAI-compatible endpoint without
changing application source. The model can be Qwen, Llama, Gemma, Mistral or
another compatible model.

## Online AI

The first-run wizard will expose supported online providers. Provider-specific
credentials are entered by the user and stored through the runtime's secret
configuration mechanism, never in Git.

## Rules

1. No API key in source control.
2. No absolute developer paths in source control.
3. No model weights in source control.
4. No runtime state in source control.
5. Provider/model selection must be replaceable without editing core agent code.
