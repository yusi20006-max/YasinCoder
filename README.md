# YasinCoder

AI coding agent with a portable, provider-agnostic architecture.

## Current status

YasinCoder is being rebuilt as a clean-clone project: runtime state, credentials, caches, logs, and local model files stay outside Git.

## Supported deployment modes

At first run, users will choose:

1. **Offline / local AI** — connect YasinCoder to their own local runtime/model (for example llama.cpp or Ollama). No model is bundled in this repository.
2. **Online AI** — choose a configured provider/model such as Gemini or another OpenAI-compatible/custom provider and supply the required API credentials.

The exact provider/model configuration is intentionally user-owned and portable.

## Architecture

- `core/` — project intelligence and reusable domain services
- `commands/` — user-facing coding operations
- `providers/` — AI provider adapters
- `config.py` — compatibility configuration layer; user/runtime values should come from environment or external config
- `docs/` — architecture, configuration, roadmap and operational documentation

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md).

## Repository rules

- Never commit GGUF/model binaries.
- Never commit API keys, tokens, local runtime state, logs or caches.
- Never depend on the developer's absolute filesystem paths.
- A clean clone must be configurable for a different local model without source edits.

## Roadmap

Execution is tracked exclusively through GitHub Issues. Phase work should be implemented against the corresponding issue and verified before that issue is closed.

See the master roadmap issue in this repository for the complete phase map.
