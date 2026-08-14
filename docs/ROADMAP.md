# YasinCoder Roadmap

This roadmap is the implementation plan for making **YasinCoder** the single canonical coding-agent project and keeping its local/cloud AI runtime under the same repository.

## Phase 0 — Repository ownership and baseline

Status: **COMPLETE**

- [x] Establish `YasinCoder` as the canonical coding-agent repository.
- [x] Keep the project implementation and runtime work under this repository.
- [x] Establish modular Python agent structure.
- [x] Establish command modules for chat, fix, review, refactor, search, project and model operations.

## Phase 1 — Local runtime foundation

Status: **COMPLETE / VERIFIED**

- [x] Local web gateway on port 18765.
- [x] Qwen local runtime on port 18080.
- [x] Qwen3 1.7B Q4_K_M loaded through llama.cpp.
- [x] Start/stop scripts.
- [x] Gateway `/api/status`.
- [x] Live logs endpoint.
- [x] Start/stop/restart HTTP control routes.
- [x] Browser UI returns HTTP 200.
- [x] Restart lifecycle verified.
- [x] Local Qwen generation verified with `QWEN_OK`.

## Phase 2 — Provider integration

Status: **IN PROGRESS**

- [x] `/api/qwen` gateway integration.
- [x] `/api/gemini` gateway integration.
- [x] Gemini CLI discovery/status.
- [x] Provider-independent gateway contract.
- [x] Termux ripgrep installation.
- [ ] Fix/verify Gemini CLI environment detection for `rg`.
- [ ] Normalize provider errors: quota, timeout, auth, network, model unavailable.
- [ ] Add provider health state with `online`, `ready`, `degraded`, `quota_exhausted`, `offline`.
- [ ] Add configurable provider priority/fallback chain.
- [ ] Add request timeout and cancellation.
- [ ] Add structured request/response telemetry without storing secrets.

## Phase 3 — Coding-agent execution core

Status: **NEXT**

- [ ] Define a stable provider interface.
- [ ] Define tool execution interface.
- [ ] Project discovery and workspace model.
- [ ] Safe file read/write/edit operations.
- [ ] Patch/diff generation and validation.
- [ ] Command execution policy and approvals.
- [ ] Test runner abstraction.
- [ ] Git status/diff/branch/commit operations.
- [ ] Session and conversation state.

## Phase 4 — Project intelligence

- [ ] Complete file index.
- [ ] Symbol/function/class index.
- [ ] Import/dependency graph.
- [ ] Code search and semantic search.
- [ ] Project memory.
- [ ] Change-impact analysis.
- [ ] Architecture-aware context selection.

## Phase 5 — Agent workflows

- [ ] Chat → inspect → plan → edit → test loop.
- [ ] Fix workflow.
- [ ] Review workflow.
- [ ] Refactor workflow.
- [ ] Explain workflow.
- [ ] Autonomous bounded task execution.
- [ ] Checkpoint/rollback.
- [ ] Human approval gates for destructive actions.

## Phase 6 — Local AI maturity

- [ ] Benchmark Qwen 1.7B against representative coding tasks.
- [ ] Evaluate larger Qwen/local coding models within device RAM limits.
- [ ] Model registry and metadata.
- [ ] Dynamic context sizing.
- [ ] Streaming responses.
- [ ] Quantization/model compatibility checks.
- [ ] CPU/GPU/accelerator detection where available.

## Phase 7 — Cloud and fallback orchestration

- [ ] Gemini provider.
- [ ] Additional OpenAI-compatible providers.
- [ ] Provider credentials isolated from repository files.
- [ ] Priority chain.
- [ ] Retry policy based on error class.
- [ ] Circuit breaker.
- [ ] Quota-aware routing.
- [ ] Local-first/offline mode.

## Phase 8 — Web control plane

- [ ] Model selector.
- [ ] Provider health dashboard.
- [ ] Live logs with filtering.
- [ ] Start/stop/restart controls.
- [ ] Chat interface.
- [ ] Project/workspace selector.
- [ ] Task execution view.
- [ ] Diff/test approval view.

## Phase 9 — Security and reliability

- [ ] Remove duplicate route branches.
- [ ] Authentication for remote access.
- [ ] Restrictive CORS.
- [ ] Rate limiting.
- [ ] Command allowlist/approval model.
- [ ] Secret redaction.
- [ ] Process/PID ownership hardening.
- [ ] Crash recovery.
- [ ] Health/readiness/liveness separation.
- [ ] Automated regression suite.

## Phase 10 — Production packaging

- [ ] One-command install for Termux/Linux.
- [ ] One-command start/stop/status.
- [ ] Configuration file with documented defaults.
- [ ] Model installation helper.
- [ ] Backup/restore.
- [ ] Versioned releases.
- [ ] CI checks.
- [ ] Release artifacts.

## Definition of done

YasinCoder is considered production-ready when a fresh installation can:

1. discover a project safely;
2. start the selected local/cloud provider;
3. execute a coding task through a stable provider interface;
4. inspect and modify files with checkpoints;
5. run tests and present failures clearly;
6. show a reviewable diff;
7. recover from provider/process failure;
8. operate offline with a local model when configured;
9. keep secrets and destructive operations protected;
10. document every public integration contract.
