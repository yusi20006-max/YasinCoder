# Cloudflare Worker gateway

This Worker exposes the same OpenAI-compatible routes used by the local gateway:

- `GET /health` and `GET /api/status`
- `GET /v1/models` and `/api/models`
- `POST /v1/chat/completions` and `/api/chat`

## Configuration

Set secrets with Wrangler; do not commit them:

- `YASIN_WORKER_API_KEY` — client authentication key.
- `YASIN_UPSTREAM_API_KEY` — credential sent only to the configured upstream.

Set non-secret variables in `wrangler.toml` or the Cloudflare dashboard:

- `YASIN_UPSTREAM_URL` — OpenAI-compatible upstream base URL.
- `YASIN_MODEL` — model name returned by `/v1/models`.
- `YASIN_ALLOWED_ORIGINS` — comma-separated browser origin allowlist.
- `YASIN_MAX_BODY_BYTES` — request-size ceiling, capped by the Worker at 16 MiB.
- `YASIN_RATE_LIMIT_PER_MINUTE` — per-IP in-memory request ceiling.

## Deploy

```sh
cd worker
wrangler secret put YASIN_WORKER_API_KEY
wrangler secret put YASIN_UPSTREAM_API_KEY
wrangler deploy
```

Set `YASIN_UPSTREAM_URL` and other non-secret values before deploying. The Worker never sends its client authentication key upstream and never includes upstream credentials in responses.

The rate limiter is intentionally best-effort and in-memory. For strict distributed quotas, put a Cloudflare-native rate limiting product or Durable Object in front of the Worker.

## Rate limiting

The Worker prefers the optional Cloudflare-native Rate Limiting binding YASIN_RATE_LIMITER. The binding is configured in worker/wrangler.toml with a positive account-scoped namespace ID and a 60-second window. Cloudflare documents that this API is fast and backed by Cloudflare infrastructure, but its counters are local to the Cloudflare location and eventually consistent; it is therefore a distributed edge control, not an exact global quota.

If the native binding is unavailable, the Worker retains the bounded in-memory limiter as a compatibility fallback. If a configured native limiter fails at runtime, the Worker fails closed with HTTP 503 rather than silently bypassing abuse protection.

Cloudflare recommends stable actor identifiers such as API keys for rate-limit keys; the Worker uses the authenticated bearer credential when present and otherwise falls back to the client IP for anonymous compatibility traffic.

Before production deployment, choose a namespace ID that is intentionally unique for this Worker/account. Wrangler 4.36.0 or later is required for the Rate Limiting API.
