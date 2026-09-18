# Changelog

## 0.2.0

- Completed the production Terminal UI acceptance audit with deterministic coverage for non-interactive, invalid-input, and task-recovery behavior.
- Hardened provider/runtime reliability with normalized malformed-response handling across OpenAI-compatible, Ollama, and Cloudflare adapters.
- Added a provider/runtime reliability matrix with explicit PASS and NOT TESTED evidence boundaries.
- Hardened sandbox subprocess output capture so configured output limits are enforced without unbounded pipe buffering.
- Added adversarial symlink-escape and output-limit regression coverage.
- Added stable Linux, macOS, and Windows platform integration CI coverage while keeping native Termux/Android execution explicitly separate.
- Added optional Cloudflare-native Rate Limiting binding support with fail-closed behavior when a configured limiter is unavailable.
- Added bounded, secret-safe production diagnostics and GitHub/TUI diagnostic redaction.
- Preserved externalized credentials, local/offline isolation, capability gates, and clean-clone packaging.

## 0.1.0

- Added canonical semantic version metadata in `VERSION`.
- Added Python packaging metadata for clean-clone builds.
- Added release checklist, configuration migration and rollback policy.
- Added tagged GitHub release automation with source/wheel artifacts and SHA-256 checksums.
- Confirmed release artifacts do not package GGUF models, credentials or runtime state.

## 0.1 Alpha

Initial architecture

Project scanner

Brain

Commands

Provider system

Cloudflare gateway ready

Prompt system

Review

Explain

Fix

Refactor

## Phase 6

- Added workspace-confined file operations.
- Added deny-by-default capability permissions for write, execute, network, git, and admin actions.
- Added dry-run plus explicit approval semantics for file mutations.
- Added bounded subprocess execution with process-group cleanup on timeout.
- Added structured tool audit records and security documentation.
