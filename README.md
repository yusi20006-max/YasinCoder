# YasinCoder

AI coding agent with a portable, provider-agnostic architecture.

## Current status

YasinCoder is being rebuilt as a clean-clone project: runtime state, credentials, caches, logs, and local model files stay outside Git.

## Installation

YasinCoder is a normal Python distribution and can be installed from a clean clone:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
```

For development/editable installs:

```bash
python -m pip install -e .
```

After installation, both the public package and CLI are available outside the repository directory:

```bash
python -c "import yasincoder; print(yasincoder.__version__)"
yasincoder info
```

On Windows, activate the virtual environment with `.venv\\Scripts\\activate` instead of `. .venv/bin/activate`.

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
- `docs/` — architecture, configuration, gateway and operational documentation

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md) and [`docs/GATEWAY.md`](docs/GATEWAY.md).

## Repository rules

- Never commit GGUF/model binaries.
- Never commit API keys, tokens, local runtime state, logs or caches.
- Never depend on the developer's absolute filesystem paths.
- A clean clone must be configurable for a different local model without source edits.

## Verification

From a fresh clone:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

To verify the distribution boundary itself:

```bash
python -m pip install .
python -c "import yasincoder"
yasincoder info
```

The deterministic suite includes gateway contract/security tests, packaging smoke coverage, and clean-clone invariants for model portability and developer-path isolation.

## Roadmap

Execution is tracked exclusively through GitHub Issues. Phase work should be implemented against the corresponding issue and verified before that issue is closed.

See the master roadmap issue in this repository for the complete phase map.
