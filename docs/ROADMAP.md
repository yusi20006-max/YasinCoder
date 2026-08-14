# YasinCoder Roadmap

## Product goal

YasinCoder is a portable, provider-agnostic AI coding platform. A clean clone must let each user choose and configure their own AI backend without source changes or bundled developer runtime/model state.

## Delivery principles

- No GGUF/model binaries in Git.
- No developer-specific absolute paths, ports, credentials, caches or logs.
- Offline/local AI and online AI are first-class modes.
- Local model selection is user-owned and portable.
- Online provider configuration is user-owned and credential-aware.
- Work is tracked through GitHub Issues; implementation should land through the corresponding issue PR.
- Every completed phase must have tests and documentation evidence.

## Phase map

| Phase | Scope | Status |
|---|---|---|
| 0 | Repository architecture and project baseline | Complete |
| 1 | Generic local AI/provider adapter | Complete |
| 2 | Model manager and portable configuration | Complete |
| 3 | Universal AI gateway | Complete |
| 4 | Smart routing and fallback | Complete |
| 5 | Coding-agent engine and tools | Complete |
| 6 | Sandboxed execution and permissions | Complete |
| 7 | Workspace/project/session management | Complete |
| 8 | PWA/mobile-first UI | Complete |
| 9 | Installer and first-run wizard | Complete |
| 10 | Cross-platform support | Complete |
| 11 | Security hardening | Complete |
| 12 | Automated/unit/integration/E2E testing | Complete |
| 13 | YASIN-DOCS documentation synchronization | In progress |
| 14 | Release engineering and versioning | Planned |
| 15 | Clean-clone production audit and v1.0 | Planned |

## Phase 13 documentation contract

YASIN-DOCS is the canonical source for ecosystem-level architecture and cross-project decisions. YasinCoder remains the source of truth for implementation. When a YasinCoder change affects system boundaries, responsibilities, dependencies, or public contracts, both the project documentation and the relevant YASIN-DOCS architecture/ADR records must be updated.

Phase 13 must document:

- architecture and repository boundaries;
- local model portability and the no-bundled-model rule;
- offline/online first-run choices;
- provider and gateway behavior;
- coding-agent/tool boundaries;
- security model;
- deterministic and provider-dependent testing;
- troubleshooting and known environment limitations;
- release and compatibility expectations;
- current roadmap/status.

## Definition of Done

A clean clone can install without the developer's local model, configure its own AI backend, run locally or remotely according to user configuration, pass deterministic tests, and follow the documented architecture.
