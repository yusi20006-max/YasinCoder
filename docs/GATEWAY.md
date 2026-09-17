# YasinCoder Gateway

The gateway is the application boundary between clients and configured AI providers.

## Local gateway

The default server binds to `127.0.0.1` and exposes:

- `GET /health`
- `GET /api/status`
- `GET /v1/models` / `GET /api/models`
- `GET /v1/routing` / `GET /api/routing`
- `POST /v1/chat/completions` / `POST /api/chat`

Health is public. Model, routing, and chat routes are protected when `YASIN_API_KEY` is configured.

A chat request uses the OpenAI-style shape:

```json
{
  "model": "auto",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

Streaming requests set `"stream": true` and receive server-sent events. Provider failures are normalized; internal exception details and credentials are not returned.

## Security

`YASIN_ALLOWED_ORIGINS` controls browser-origin access and `YASIN_MAX_BODY_BYTES` controls request size. Tool execution is independently protected by permission policy, workspace confinement, shell-control rejection, timeout limits, and output limits.

For remote exposure, use an authenticated network boundary and TLS rather than binding the local gateway directly to an untrusted interface.

## Cloudflare Worker

The optional Worker in `worker/` exposes the same health/models/chat route family and forwards chat requests to a configured OpenAI-compatible upstream. It keeps `YASIN_WORKER_API_KEY` and `YASIN_UPSTREAM_API_KEY` server-side, supports streaming pass-through, validates origins, limits request size, and applies a best-effort per-IP rate limit.

Deploy with Wrangler using the instructions in `worker/README.md`. `YASIN_UPSTREAM_URL`, `YASIN_MODEL`, and `YASIN_ALLOWED_ORIGINS` are non-secret configuration; credentials should be Cloudflare secrets.

## Provider independence

The gateway does not bundle a model or assume a developer filesystem path. Users configure their own provider/model registry or environment variables. Supported provider types are documented in `docs/CONFIGURATION.md`.

## Verification

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

CI additionally checks the Worker with Node syntax validation and verifies its deployment contract.
