# YasinCoder

**YasinCoder** is the unified AI coding agent platform for local and remote model execution.

The repository is intentionally the single home for the product: agent runtime, project intelligence, providers, local AI gateway, web UI, coding tools, tests, and deployment assets.

## Current architecture

- **Agent:** project analysis and coding workflows.
- **Providers:** Cloudflare and local Gateway provider.
- **Local Gateway:** stable HTTP boundary for Qwen/llama.cpp and future local/remote routing.
- **Project intelligence:** scan, index, search, context, dependency and symbol data.
- **Coding tools:** explain, review, refactor, fix, read and search.

## Local AI

The local provider connects to the YasinCoder Gateway by default:

```text
YasinCoder -> http://127.0.0.1:18765/api/qwen -> Qwen/llama.cpp
```

Configure with environment variables:

```bash
export YASIN_MODEL=local
export YASIN_GATEWAY_URL=http://127.0.0.1:18765
```

The gateway owns model process lifecycle. YasinCoder should not directly spawn or manage llama.cpp.

## Provider modes

- `local` — local Qwen through the gateway.
- `cloudflare` — Cloudflare Workers AI.
- `auto` — provider selection/fallback policy.

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Status

The project started as an Alpha coding agent. The current work is consolidating the previously separate local AI gateway into this repository and turning YasinCoder into the single product boundary.
