# YasinCoder Configuration Contract

YasinCoder keeps provider configuration in a user-owned registry outside the repository.

## Model registry

The default file is `~/.config/yasin-coder/models.json` on Linux/Termux and follows `XDG_CONFIG_HOME` when set. Override it with `YASIN_MODELS_FILE`.

A model entry has a stable `name`, provider `type`, optional `model`, `base_url`, `aliases`, `timeout`, `temperature`, `max_tokens`, and provider metadata. Supported types are `openai_compatible`, `openai`, `custom`, `ollama`, `llama_cpp`, and `cloudflare`.

Example:

```json
{
  "version": 2,
  "default": "local",
  "models": [
    {
      "name": "local",
      "type": "ollama",
      "model": "qwen3",
      "aliases": ["qwen"],
      "timeout": 120,
      "temperature": 0.2,
      "max_tokens": 4096
    }
  ]
}
```

## Environment variables

| Variable | Purpose |
|---|---|
| `YASIN_PROJECT_PATH` | Workspace/project root |
| `YASIN_MODEL` | Provider/model selection by name or alias |
| `YASIN_MODEL_NAME` | Model advertised by `YASIN_BASE_URL` |
| `YASIN_BASE_URL` | OpenAI-compatible/custom endpoint |
| `YASIN_API_KEY` | Credential, referenced as `api_key_env` |
| `YASIN_TEMPERATURE` | Generation temperature |
| `YASIN_MAX_TOKENS` | Output token budget |
| `YASIN_TIMEOUT` | Provider request timeout |
| `CF_ACCOUNT_ID` | Cloudflare account, referenced as `account_id_env` |
| `CF_API_TOKEN` | Cloudflare credential, referenced as `api_token_env` |
| `CF_MODEL` | Cloudflare model |

## Secrets

Never put API keys or tokens in `models.json`. Use environment references such as `api_key_env`, `api_token_env`, or `account_id_env`. The registry stores only the variable name; runtime code resolves the value from the process environment.

```bash
export YASIN_BASE_URL=https://example.invalid/v1
export YASIN_MODEL_NAME=my-model
export YASIN_API_KEY='...'
```

## Selection

Selection order is deterministic:

1. `YASIN_MODEL` when it matches a model name or alias.
2. The persisted `default` entry.
3. The first model sorted by name.

Run `python main.py models` to inspect the registry without printing secret values. Run `python main.py doctor` to validate configuration and get first-run guidance.

## Discovery

YasinCoder can discover a configured `YASIN_BASE_URL` endpoint and local models exposed by llama.cpp (`127.0.0.1:18080`) or Ollama (`127.0.0.1:11434`). Discovery writes only non-secret model metadata and environment-variable references to the user registry.

## Rules

1. No API key in source control.
2. No absolute developer paths in source control.
3. No model weights in source control.
4. No runtime state in source control.
5. Provider/model selection must be replaceable without editing core agent code.
