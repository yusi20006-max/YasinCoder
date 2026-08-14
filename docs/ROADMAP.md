# YasinCoder Unified Roadmap

## Phase 0 — Repository consolidation

- Make `YasinCoder` the single product and repository.
- Keep all gateway, UI, agent, provider, tools, tests, and deployment assets here.
- Define boundaries and migration rules.
- Preserve backups and avoid destructive history changes.

## Phase 1 — Gateway parity

- Migrate the working `gemini-web` gateway into `gateway/`.
- Preserve Qwen lifecycle management, health, logs, start/stop/restart, and UI.
- Add deterministic smoke tests.
- Add local-only default binding and configurable authentication for non-local use.

## Phase 2 — Provider unification

- Connect `LocalProvider` to the YasinCoder Gateway.
- Keep Cloudflare provider working.
- Add Gemini provider/routing behind the same abstraction.
- Implement health-aware fallback policy.
- Normalize provider responses and errors.

## Phase 3 — Agent runtime

- Replace one-shot prompt execution with a controlled agent loop.
- Add planning, context assembly, tool selection, execution, verification, and final response stages.
- Add explicit iteration/time/token limits.

## Phase 4 — Coding tools

- Safe file read/search.
- Patch/write with backups.
- Git status/diff and branch awareness.
- Test runner with timeouts.
- Structured tool results.
- Approval gates for destructive operations.

## Phase 5 — Project intelligence

- Project scan/index.
- Dependency and symbol graph.
- Persistent project memory.
- Context selection and caching.
- Session restore.

## Phase 6 — Autonomous coding

- Plan -> edit -> test -> diagnose -> fix -> retest.
- Failure budgets and rollback.
- Checkpointing.
- Human approval for risky changes.

## Phase 7 — Multi-agent and automation

- Specialist agents.
- Parallel task execution where safe.
- Documentation/test generation.
- GitHub integration and PR workflow.

## Phase 8 — Release hardening

- CI matrix.
- Security audit.
- Secret scanning.
- Performance and resource limits for Android/Termux.
- Versioned configuration and migration.
- Reproducible installation.

## Current execution order

1. Provider bridge: **started**.
2. Gateway migration into this repository.
3. End-to-end local Qwen test from YasinCoder.
4. Gemini/Cloudflare routing and fallback.
5. Agent tools and controlled edit loop.
