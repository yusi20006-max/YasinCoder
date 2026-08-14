# YasinCoder installation and first run

YasinCoder is designed for clean clones. The repository does not contain a developer machine path, API key, or model weights.

## Quick start

```bash
./install.sh
```

The installer checks Python 3.10+ and Git, then launches the first-run wizard.

## AI mode

The wizard asks the user to choose:

1. **Offline** — configure a user-owned local runtime such as llama.cpp, Ollama, or another OpenAI-compatible local endpoint.
2. **Online** — configure a provider such as Gemini or another compatible API.

Model identifiers, endpoints, fallbacks, and secrets are runtime data and are stored outside Git by default at `~/.config/yasin-coder/`.

## Diagnostics

```bash
python3 scripts/bootstrap.py doctor
```

## Reset

```bash
python3 scripts/bootstrap.py reset
```

Reset removes only the external YasinCoder runtime configuration. It does not delete repository files or user-owned model files.

## Environment overrides

- `YASIN_CONFIG_DIR` — external runtime configuration directory.
- `YASIN_API_KEY` — optional secret supplied by the environment rather than stored in Git.
- Existing `config.example` documents provider/model variables.

## Local model policy

No GGUF, SafeTensors, model directory, or device-specific model path is downloaded or required by installation. Each user chooses and configures their own model/runtime.
