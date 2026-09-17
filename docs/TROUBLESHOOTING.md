# Troubleshooting

## `yasincoder: command not found`

Activate the virtual environment or install the package into the active Python environment:

```bash
. .venv/bin/activate
python -m pip install .
```

Verify with `yasincoder info`.

## `doctor` says no model is configured

Configure a provider through environment variables or the user-owned model registry. For an OpenAI-compatible endpoint:

```bash
export YASIN_BASE_URL="https://provider.example/v1"
export YASIN_MODEL_NAME="your-model"
export YASIN_API_KEY="your-api-key"
yasincoder doctor
yasincoder models
```

The credential value is read at runtime and must never be committed.

## Local Ollama

Start Ollama separately, ensure the selected model exists, then configure/select the Ollama model in the user registry. YasinCoder does not install or bundle the local model runtime.

## Local llama.cpp

Run the llama.cpp OpenAI-compatible server separately and point the YasinCoder model entry at its base URL. The model weights remain outside the repository.

## Gateway authentication failure

If `YASIN_API_KEY` is set, protected routes require `Authorization: Bearer <key>`. Health endpoints remain public. If an allowed-origin list is configured, browser requests must originate from one of those exact origins.

## Gateway payload too large

Increase `YASIN_MAX_BODY_BYTES` only when required. The value is clamped to a safe range and large requests should generally be reduced instead.

## Autonomous command denied

Pass explicit permissions for the required capability. The default policy denies side effects. Shell control operators and workspace escapes are rejected regardless of normal execution permission.

## Cloudflare Worker returns `upstream_error`

Check that `YASIN_UPSTREAM_URL` is set and reachable from Cloudflare, and that `YASIN_UPSTREAM_API_KEY` is configured as a Worker secret when the upstream requires authentication. Client authentication uses a separate `YASIN_WORKER_API_KEY`.

## Tests

From the repository root:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

The CI workflow also validates the Cloudflare Worker with Node syntax checks.
