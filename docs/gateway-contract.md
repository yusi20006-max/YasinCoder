# YasinCoder Universal AI Gateway Contract

## Purpose

YasinCoder exposes one provider-neutral contract so the UI, coding agent, and future integrations do not depend on llama.cpp, Ollama, Gemini, Cloudflare, or another provider's native API.

## Endpoints

- `GET /health` — liveness and routing metadata.
- `GET /api/status` — compatibility alias for health/status.
- `GET /v1/models` — configured model discovery.
- `GET /api/models` — compatibility alias for model discovery.
- `GET /api/routing` / `GET /v1/routing` — current routing metadata.
- `POST /v1/chat/completions` — canonical chat endpoint.
- `POST /api/chat` — compatibility alias for chat.

## Chat request

```json
{
  "model": "optional-model-name",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

`messages` is required, non-empty, and limited to 128 entries. Every message has a string `role`; content is text or structured content. `model` is optional and is resolved through configured model selection when omitted.

## Chat response

```json
{
  "id": "yasin-...",
  "object": "chat.completion",
  "created": 0,
  "model": "configured-model",
  "choices": [
    {
      "index": 0,
      "message": {"role": "assistant", "content": "..."},
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  },
  "routing": {
    "selected": "configured-model",
    "attempts": [],
    "offline": true
  }
}
```

Provider-specific metadata is not required for a valid response. Routing metadata is additive and never contains credentials or raw provider errors.

## Model discovery

Each model entry exposes:

- `id` / `name` — stable configured model identifier.
- `provider` — normalized provider type.
- `capabilities` — normalized capability list.
- `default` — whether configuration marks it as default.

No developer-local model file, device path, or credential is part of this contract.

## Error contract

All gateway errors use:

```json
{
  "error": {
    "code": "stable_machine_code",
    "message": "safe human-readable message"
  }
}
```

Canonical codes include `invalid_json`, `invalid_request`, `model_not_found`, `unauthorized`, `origin_forbidden`, `payload_too_large`, `provider_auth`, `provider_quota`, `provider_timeout`, `provider_network`, `provider_server`, `provider_model`, `provider_error`, `not_found`, and `internal_error`.

HTTP status is deterministic: 400 for malformed requests, 401 for authentication failures, 403 for origin policy failures, 404 for missing routes/models, 413 for oversized requests, 429 for provider quota, 502 for provider failures, and 503 for transient provider availability failures.

## Provider boundary

Adapters may use native APIs internally, but they must return normalized model information and raise failures that the routing layer can classify. Credentials, raw upstream bodies, and provider-specific stack traces must never be returned to clients.

The canonical implementation lives in `core/gateway_contract.py`; gateway routing consumes it through `gateway.py`.
