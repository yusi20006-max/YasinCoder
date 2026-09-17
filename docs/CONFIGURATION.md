# YasinCoder Configuration Contract

YasinCoder keeps provider configuration in a user-owned registry outside the repository.

## First-run Gemini setup

For the simplest online setup, run:

```bash
yasincoder setup gemini
```

The command prompts for a Gemini API key without echoing it, validates the key against Google's OpenAI-compatible model endpoint, discovers compatible Gemini models, selects a supported Flash model, and persists `gemini` as the default provider. The key is stored separately in a user-only credential file; it is never written to `models.json`, printed, logged, or committed.

The default Gemini endpoint is `https://generativelanguage.googleapis.com/v1beta/openai`. Google documents this OpenAI-compatible interface, including model listing and streaming.

The credential file defaults to `~/.config/yasin-coder/gemini.key` on Linux/Termux and can be relocated with `YASIN_GEMINI_CREDENTIAL_FILE`.

## Model registry

The default file is `~/.config/yasin-coder/models.json` on Linux/Termux and follows `XDG_CONFIG_HOME` when set. Override it with `YASIN_MODELS_FILE`.

A model entry has a stable `name`, provider `type`, optional `model`, `base_url`, `aliases`, `timeout`, `temperature`, `max_tokens`, and provider metadata. Supported types are `openai_compatible`, `openai`, `custom`, `ollama`, `llama_cpp`, `cloudflare`, and `gemini`.

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
| `YASIN_GEMINI_CREDENTIAL_FILE` | Optional path for the user-only Gemini credential file |
| `YASIN_TEMPERATURE` | Generation temperature |
| `YASIN_MAX_TOKENS` | Output token budget |
| `YASIN_TIMEOUT` | Provider request timeout |
| `CF_ACCOUNT_ID` | Cloudflare account, referenced as `account_id_env` |
| `CF_API_TOKEN` | Cloudflare credential, referenced as `api_token_env` |
| `CF_MODEL` | Cloudflare model |

## Secrets

Never put API keys or tokens in `models.json`. Use environment references such as `api_key_env`, `api_token_env`, or `account_id_env`, or a file reference such as `api_key_file_env` for credentials created by the Gemini setup flow. Runtime code resolves the value only when creating the provider adapter.

## Selection

Selection order is deterministic:

1. `YASIN_MODEL` when it matches a model name or alias.
2. The persisted `default` entry.
3. The first model sorted by name.

Run `yasincoder setup gemini` for the first-run Gemini flow, `yasincoder models` to inspect the registry without printing secret values, and `yasincoder doctor` to validate configuration.

## Discovery

YasinCoder can discover a configured `YASIN_BASE_URL` endpoint and local models exposed by llama.cpp (`127.0.0.1:18080`) or Ollama (`127.0.0.1:11434`). Discovery writes only non-secret model metadata and environment-variable references to the user registry.

## Rules

1. No API key in source control.
2. No secret value in `models.json`.
3. No absolute developer paths in source control.
4. No model weights in source control.
5. No runtime state in source control.
6. Provider/model selection must be replaceable without editing core agent code.
