# Provider and Runtime Reliability Matrix

This matrix records deterministic repository-level verification for the supported provider types. Live network/provider credentials are not assumed by CI.

| Provider/runtime | Discovery | Configuration/auth | Streaming | Malformed response | Offline | Live verification |
|---|---|---|---|---|---|---|
| Gemini | PASS via mocked OpenAI-compatible discovery | PASS via file/env credential contract | PASS through OpenAI-compatible adapter | PASS | N/A | NOT TESTED |
| OpenAI-compatible | PASS via mocked /v1/models | PASS | PASS via SSE contract | PASS | N/A | NOT TESTED |
| OpenAI | PASS through the OpenAI-compatible adapter contract | PASS | PASS through shared adapter | PASS | N/A | NOT TESTED |
| custom | PASS through the OpenAI-compatible adapter contract | PASS | PASS through shared adapter | PASS | N/A | NOT TESTED |
| Ollama | PASS via mocked /api/tags | PASS | PASS via NDJSON contract | PASS | PASS | NOT TESTED |
| llama.cpp | PASS through OpenAI-compatible adapter contract | PASS | PASS through shared SSE contract | PASS | PASS | NOT TESTED |
| Cloudflare | PASS through explicit adapter contract | PASS with normalized auth/rate-limit failures | PASS via Worker AI streaming contract | PASS | N/A | NOT TESTED |

## Reliability contract

- Credentials remain external: environment or file references are resolved only at runtime.
- Authentication and configuration failures do not trigger provider fallback.
- Transient network, timeout, server, quota, rate-limit, and unavailable failures may advance to the next configured online provider.
- Offline/local providers never silently fall back to an online provider.
- Provider responses with invalid JSON or an unexpected top-level shape are normalized to ProviderRequestError rather than leaking implementation exceptions.
- Streaming parsers ignore malformed individual events and continue until completion or transport failure.
- Live provider verification is intentionally NOT TESTED when credentials or a reachable runtime are unavailable; mocked contract coverage is not presented as live verification.

## Deterministic verification

python -m unittest tests.test_provider_adapters tests.test_model_manager tests.test_routing tests.test_gemini_setup -v
