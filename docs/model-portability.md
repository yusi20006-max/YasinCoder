# Portable model configuration

YasinCoder does not require the developer's local GGUF file, model path, or runtime. A clone stores machine-specific model definitions outside Git.

## Registry

Default location:

`~/.config/yasin-coder/models.json`

Override it with `YASIN_MODELS_FILE`.

Each model entry contains at least `name` and `type`. Supported runtime types are:

- `llama_cpp` — llama.cpp server exposing `/v1/chat/completions`.
- `ollama` — Ollama `/api/generate` runtime.
- `openai_compatible` — any compatible local or remote endpoint.
- `cloudflare` — optional Cloudflare Workers AI configuration.

## First run

The model manager discovers configured `YASIN_BASE_URL`, a local llama.cpp server on port `18080`, and Ollama on port `11434` when reachable. Discovered runtimes are registered and the first available runtime becomes the default if no selection exists.

## Manual model

A user can register a model without editing Python source:

```python
from models.manager import ModelManager

m = ModelManager()
m.upsert({
    "name": "my-qwen",
    "type": "llama_cpp",
    "base_url": "http://127.0.0.1:18080",
    "model": "my-qwen-model"
})
m.select("my-qwen")
```

The selection survives restart because the registry is persisted outside the repository.

## Portability rule

Never commit GGUF files, absolute home-directory paths, API keys, or machine-specific runtime state. Commit only examples and code that can discover or reference a user's own runtime.
