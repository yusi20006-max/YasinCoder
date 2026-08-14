# YasinCoder Testing Guide

## Deterministic CI

The repository's CI pipeline must not require private provider credentials, network access to a model provider, or the developer's local model weights.

CI performs:

1. Python bytecode compilation with `python -m compileall -q .`.
2. Full `unittest` discovery under `tests/`.
3. Gateway contract tests using fake model/provider objects.
4. Routing, model-manager, runtime, state-store, agent-tool, and security regression tests already present in the repository.

Run the same deterministic suite locally:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

## Optional/manual verification

Real Gemini or other cloud-provider calls are environment-dependent and must not block CI. Run those tests only when the user has configured credentials and quota.

Offline/local-model verification is also environment-dependent: CI validates the model contract through fakes; a real GGUF/llama.cpp smoke test belongs to the manual release gate.

## Clean-clone verification

A release candidate should be cloned into a fresh directory, configured from `config.example`, and then run through the deterministic suite before release. No developer-specific model files, tokens, runtime logs, or local configuration may be required.
