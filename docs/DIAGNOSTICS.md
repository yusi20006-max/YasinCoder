# Production Diagnostics

YasinCoder diagnostics are bounded and secret-safe. Supported interfaces should report a category, concise message, optional bounded detail, and whether retry is appropriate.

## Categories

- `configuration` — missing or invalid provider/runtime configuration.
- `authentication` — credentials are missing, rejected, or unauthorized.
- `permission` — a capability gate denied an operation.
- `workspace` — path or workspace confinement failed.
- `provider` — a provider returned an invalid or unsuccessful response.
- `network` — transport or availability failure.
- `timeout` — a bounded operation exceeded its time limit.
- `test` — verification/test execution failed.
- `github` — GitHub API, PR, CI, or repository workflow failure.
- `internal` — unexpected failure not safely classified elsewhere.

## Safety

Diagnostic messages and context are passed through the central redaction layer and bounded before presentation. Tokens, credentials, authorization headers, and credential-like values are not intended to appear in default diagnostics.

Diagnostics are not telemetry. YasinCoder does not send diagnostic data anywhere unless an explicitly configured external integration performs that action.

## Evidence boundaries

GitHub/CI status can be reported only from actual workflow evidence. Provider and Cloudflare live failures are not converted into synthetic PASS states. Native Termux interactive acceptance remains separate from deterministic CI coverage.