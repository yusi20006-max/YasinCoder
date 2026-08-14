# YasinCoder Security Model

## Trust boundaries

- The gateway is bound to `127.0.0.1` by default.
- Provider credentials and model definitions live outside Git.
- Local model weights are ignored by Git and are user-owned runtime data.
- The coding-agent layer must treat model output as untrusted input.

## Gateway policy

- No CORS origins are allowed unless `YASIN_ALLOWED_ORIGINS` is explicitly set.
- `YASIN_API_KEY` enables Bearer-token authentication for all gateway routes.
- Request bodies are capped by `YASIN_MAX_BODY_BYTES` (1 MiB by default).
- JSON requests must be objects and model identifiers are length-limited.
- Static file paths are resolved and constrained beneath the web root.
- Security headers are emitted on gateway responses.

## Remote exposure

Do not bind the gateway to a public interface without authentication and an explicit origin policy. A reverse proxy, TLS termination, firewall, and network access control should be used for production remote deployments.

## Secrets

Never commit API keys, provider tokens, model credentials, local model weights, runtime state, or logs. Use environment variables or an external runtime configuration file.

## Threats addressed in Phase 11

- Cross-origin browser abuse
- Unauthenticated remote API access
- Oversized request bodies
- Malformed JSON and oversized model identifiers
- Static path traversal
- Accidental secret/model artifact commits

## Remaining agent-execution boundary

Future sandboxed execution must use explicit workspace allowlists, command allowlists/deny-lists, timeouts, resource limits, and user approval for privileged operations. Provider output must never be treated as a trusted shell command by default.
