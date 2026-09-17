# GitHub Mode

GitHub Mode is an optional integration layer between YasinCoder and GitHub. It is intentionally separate from the TUI and autonomous planner.

## Security model

Remote mutations are **deny-by-default**. The following capabilities are independent:

- `read`
- `issue_write`
- `branch_write`
- `push`
- `pr_write`
- `merge`

Only explicitly enabled capabilities may perform their operation. `merge` is never implied by another capability.

## Configuration

Authentication and repository identity are read from environment variables and are not persisted by YasinCoder:

```text
GITHUB_TOKEN
YASIN_GITHUB_OWNER
YASIN_GITHUB_REPO
YASIN_GITHUB_API_URL
YASIN_GITHUB_TIMEOUT
YASIN_GITHUB_READ
YASIN_GITHUB_ISSUE_WRITE
YASIN_GITHUB_BRANCH_WRITE
YASIN_GITHUB_PUSH
YASIN_GITHUB_PR_WRITE
YASIN_GITHUB_MERGE
```

Boolean capability variables accept `1`, `true`, or `yes` (case-insensitive).

## Current foundation

`github_mode.py` provides a small standard-library REST client, explicit capability enforcement, repository identity validation, safe error redaction, and an in-memory audit trail. It does not write credentials, tokens, model data, or a local GitHub cache.

Later Issues extend this foundation with Issues, branches/workspace, commit/push, pull requests, Actions/CI, and the final end-to-end workflow.

## MCP / Context7

When developing against GitHub API behavior or related third-party interfaces, use MCP/Context7 where available to consult current official documentation. Do not treat generated examples as authoritative when an official API contract is available.
