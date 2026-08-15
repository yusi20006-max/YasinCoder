# YasinCoder

Portable, provider-agnostic AI coding agent.

## Current status

Version: 0.1 Alpha

### AI provider architecture

YasinCoder separates the coding-agent layer from the AI runtime. A clone does **not** require the developer's model, device paths, or local runtime.

Supported provider families:

- **Local** — OpenAI-compatible local servers such as llama.cpp and other compatible runtimes.
- **Ollama** — supported through the same local-provider contract.
- **Cloudflare** — existing remote provider support.

The local model name, endpoint, runtime and timeout are user configuration. No GGUF/model binary is bundled or committed.

Example environment variables:

```text
YASIN_AI_PROVIDER=local
YASIN_LOCAL_RUNTIME=openai
YASIN_LOCAL_BASE_URL=http://127.0.0.1:18080
YASIN_LOCAL_MODEL=your-model-name
```

Copy `.env.example` as a reference and keep secrets/runtime state outside Git.

## Features

- Project Scan
- Project Brain
- File Search
- Explain
- Review
- Refactor
- Fix
- Provider system
- Generic local AI adapter
- Cloudflare gateway
- Modular architecture
- Deterministic source documentation and project reports

## Local model portability

For llama.cpp, point `YASIN_LOCAL_BASE_URL` at its OpenAI-compatible `/v1` API and set `YASIN_LOCAL_MODEL` to the alias exposed by that server. The model file itself remains outside the repository and can be any compatible model selected by the user.

For Ollama, set `YASIN_LOCAL_RUNTIME=ollama`, point `YASIN_LOCAL_BASE_URL` at the Ollama server, and set `YASIN_LOCAL_MODEL` to the installed model name.

## Documentation and project reports

The `docs` command analyzes Python source with the standard-library AST parser and never imports application code. Runtime directories, environment files, model registries and build artifacts are excluded.

```bash
python main.py docs api
python main.py docs architecture
python main.py docs report
python main.py docs changes --base HEAD^
python main.py docs all
```

`docs all` writes only generator-owned files under `docs/generated/`:

- `api.md` — source-derived API inventory
- `architecture.md` — deterministic module/import map
- `report.json` — project metrics and changed-file summary
- `changes.json` — bounded git change summary

A single report can be written elsewhere with `--output FILE`. Hand-written documentation outside `docs/generated/` is never overwritten.

## Tests

Run:

```bash
python -m unittest discover -s tests -v
```
