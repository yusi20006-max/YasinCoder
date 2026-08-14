# YasinCoder Architecture

## 1. Product boundary

YasinCoder is the coding-agent product. It owns project analysis, coding tools, AI provider abstraction, execution policy, sessions, and the mobile/web control surface.

Yasin AI remains a separate AI/runtime project. Shared concepts may be documented, but YasinCoder does not depend on Yasin AI's private runtime state.

## 2. Runtime layers

```text
User / PWA
    |
    v
Universal Gateway / Application API
    |
    +--> Routing & policy
    |       |
    |       +--> Local provider (user-selected runtime/model)
    |       +--> Online provider (Gemini / compatible / custom)
    |
    +--> Coding Agent Engine
            |
            +--> Workspace / project services
            +--> File/search/edit tools
            +--> Git tools
            +--> Test/build tools
            +--> Permission & sandbox policy
```

## 3. Repository boundaries

- `core/`: reusable project intelligence and domain services.
- `commands/`: user operations and command orchestration.
- `providers/`: provider adapters; no provider should own application state.
- `docs/`: implementation and operational documentation.
- `tests/`: deterministic unit/integration/E2E verification as the test suite grows.
- Runtime data belongs outside Git: models, credentials, caches, logs, sessions and backups.

## 4. AI boundary

The application talks to a provider-neutral contract. A local model is an implementation detail selected by the user. The repository must not assume Qwen, a particular GGUF, llama.cpp, a specific port, or a developer filesystem path.

The same UI and agent workflow must work whether the selected backend is local/offline or online.

## 5. First-run contract

The eventual first-run wizard presents two top-level choices:

- **Offline/local**: discover or configure a local runtime, then register the user's model/endpoint.
- **Online**: choose a supported provider/model, then collect only the credentials/configuration required by that provider.

The wizard writes user-owned configuration outside the repository.

## 6. Security boundary

The default deployment is localhost-only. Remote access, network-enabled tools, shell execution, Git mutation and other sensitive operations are explicit capabilities governed by later permission/sandbox phases.

Secrets must never be emitted into logs, UI responses, commits or documentation.

## 7. Clean-clone invariant

A clean clone must contain enough source and templates to install and configure YasinCoder, but never require the developer's model, credentials, absolute paths or runtime state.
