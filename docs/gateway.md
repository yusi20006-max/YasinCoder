# YasinCoder Universal AI Gateway

YasinCoder exposes a provider-neutral HTTP contract so the UI and agent do not need to know whether the selected backend is local or cloud.

## Endpoints

- `GET /health` — service health and current routing state.
- `GET /v1/models` — configured models with provider and capability metadata.
- `POST /v1/chat/completions` — OpenAI-compatible chat request/response shape.
- `GET /api/status` — compatibility health route.
- `GET /api/models` — compatibility model listing.
- `GET /api/routing` — last routing decision and sanitized attempt outcomes.
- `POST /api/chat` — compatibility chat route.

## Request

```json
{
  "model": "my-model",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

The model is optional when the configured default should be used. Unknown explicit models return a normalized `model_not_found` error.

## Routing and fallback

Each external model definition may contain an ordered `fallbacks` list. The router de-duplicates names and never follows fallback references recursively, preventing loops.

Only transient `timeout`, `network`, and server failures advance to the next fallback. Authentication failures, quota/rate-limit responses, missing models, invalid configuration, and other non-transient failures stop immediately. This prevents quota exhaustion from becoming an infinite retry loop.

When `offline: true` is set on the selected model, the chain contains only that model. Cloud providers are never contacted in offline mode.

Routing decisions are exposed through `/api/routing` and the `routing` field of successful chat responses. Logs contain only provider names and sanitized failure classes; credentials and raw provider payloads are not emitted by the router.

## Runtime configuration

No model weights, API keys, or device-specific paths belong in Git. `ProviderManager` resolves the user's configured local runtime (for example llama.cpp or Ollama) or cloud provider.

The gateway binds to localhost by default. Remote exposure and authentication belong to the security phase.

## Compatibility

The legacy `/api/*` routes are intentionally thin compatibility aliases. New clients should use `/v1/*` so the provider implementation can change without changing the client contract.
