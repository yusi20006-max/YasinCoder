# YasinCoder Architecture

YasinCoder is the single product/repository for the coding agent, AI gateway, local model runtime integration, tools, UI, and automation.

## Product boundary

Everything required to run the YasinCoder experience belongs in this repository. External services are providers, not separate products.

## Target architecture

```text
YasinCoder UI / CLI
        |
        v
   Agent Runtime
        |
        v
  Provider Router
        |
        +-------------------+
        |                   |
        v                   v
 YasinCoder Gateway     Remote Providers
        |
        +-----------------------+
        |                       |
        v                       v
 Local Qwen / llama.cpp      Gemini CLI/API
```

## Gateway contract

The gateway is the stable boundary between YasinCoder and model runtimes. YasinCoder must not own llama.cpp process management directly.

Current local endpoint:

- Gateway: `http://127.0.0.1:18765`
- Qwen runtime: `http://127.0.0.1:18080`
- Qwen route: `POST /api/qwen`
- Status: `GET /api/status`
- Logs: `GET /api/logs`
- Lifecycle: `POST /api/start`, `/api/stop`, `/api/restart`

## Provider policy

- `local`: use the YasinCoder Gateway and local Qwen runtime.
- `cloudflare`: use Cloudflare Workers AI.
- `auto`: route according to configured provider availability and explicit fallback policy.
- Gemini is treated as a provider/runtime behind the gateway rather than a separate application.

## Security

- Bind local services to loopback by default.
- Never commit API keys, OAuth tokens, model credentials, or `.env` files.
- Add authentication before exposing the gateway outside localhost.
- Restrict CORS when network access is enabled.

## Migration rule

The existing standalone `gemini-web` implementation is to be migrated into this repository under the gateway/runtime area. The migration must preserve working behavior first, then refactor internals. No destructive rewrite is allowed before parity tests pass.
