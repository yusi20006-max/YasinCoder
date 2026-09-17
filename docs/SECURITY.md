# YasinCoder Security Model

## Trust boundaries

- The local gateway binds to `127.0.0.1` by default.
- Provider credentials and model definitions live outside Git.
- Local model weights are user-owned runtime data and must not enter Git.
- Model/provider output is untrusted input and must never become shell syntax implicitly.

## Credentials and redaction

Credentials are supplied through environment variables or external runtime configuration. Sensitive mapping keys and common API-key/token formats are centrally redacted from tool and gateway responses. Error messages are normalized rather than exposing provider exception details.

The gateway accepts `YASIN_API_KEY` first and `YASIN_GATEWAY_API_KEY` only as a compatibility fallback. Do not put either value in source control.

## Workspace and file policy

File paths are resolved beneath the configured workspace. `..` traversal and symlink escapes outside that workspace are rejected. Subprocesses require an existing resolved working directory.

## Command execution

Writes, execution, network, Git, and admin operations are permission-gated. Shell control operators (`;`, `&&`, `||`, pipes and redirections) are rejected. Subprocesses have bounded timeouts and output size, and timeout cleanup targets the whole process group.

## Gateway policy

- Protected routes use Bearer-token authentication when `YASIN_API_KEY` is configured.
- Origins are constrained by `YASIN_ALLOWED_ORIGINS` when configured.
- Request bodies are capped by `YASIN_MAX_BODY_BYTES`.
- Static paths are constrained beneath the web root.
- Security headers are emitted on responses.

## Cloudflare Worker

The Worker uses `YASIN_WORKER_API_KEY` for client authentication and `YASIN_UPSTREAM_API_KEY` only for the configured upstream. These are Cloudflare secrets, never client-visible. The Worker also applies origin, request-size, and best-effort per-IP rate limits.

## Rules

1. Never commit API keys, tokens, passwords, certificates, model weights, runtime state, logs, or caches.
2. Never place credential values in the model registry; reference environment variable names.
3. Keep autonomous execution inside an approved workspace.
4. Treat provider responses as untrusted data.
5. Fail closed on malformed commands, path escapes, permission failures, and resource-limit violations.
