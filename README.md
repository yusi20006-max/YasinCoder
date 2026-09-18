# YasinCoder

Portable, provider-agnostic AI coding agent for local and online models.

## Status

The repository is clean-clone oriented: credentials, runtime state, caches, logs, and model weights are user-owned and stay outside Git. The Python package, gateway, coding tools, security boundaries, CI gates, optional Cloudflare Worker, and a dependency-free Terminal UI are implemented.

## Install from a clean clone

Linux/macOS/Termux:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
yasincoder doctor
yasincoder info
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install .
yasincoder doctor
yasincoder info
```

For development, use `python -m pip install -e .`.

## Terminal UI for Termux

YasinCoder includes a lightweight interactive terminal dashboard designed for native Termux/Android and normal terminals. It uses only the Python standard library, so no rich UI dependency is required.

Launch it with:

```bash
yasincoder tui
# or
yasincoder-tui
```

The dashboard reads live information from the existing project, Git and model interfaces. It does not fabricate task, test, provider, or Git state.

Navigation:

```text
1 Dashboard       2 New Task        3 Projects
4 Sessions        5 Providers       6 Git / Changes
7 Tests           8 System Status   9 Settings
q Quit
```

The UI is intentionally keyboard-first and remains useful on narrow phone-sized terminals. ANSI rendering is automatically disabled for `NO_COLOR`, redirected output, dumb terminals, or other non-interactive contexts. Simple and advanced concepts share the same underlying state; the current interface keeps the safe simple flow visible while exposing technical state in dedicated screens.

For detailed usage, see `docs/TUI.md`.

## First-run Gemini setup

If you want Gemini as the default online AI, you do not need to manually configure an endpoint or model. Run:

```bash
yasincoder setup gemini
```

YasinCoder securely prompts for the Gemini API key, validates it, discovers compatible Gemini models, selects a supported model, and saves Gemini as the default provider. The API key is stored in a user-only credential file outside the repository and is never printed or placed in the model registry.

Google documents Gemini's OpenAI-compatible endpoint at `https://generativelanguage.googleapis.com/v1beta/openai/`, including model listing and streaming.

## First provider-backed chat

YasinCoder keeps provider credentials out of source control. For an OpenAI-compatible endpoint, configure the endpoint and model through environment variables, then run the normal CLI:

```bash
export YASIN_BASE_URL="https://provider.example/v1"
export YASIN_MODEL_NAME="your-model"
export YASIN_API_KEY="your-api-key"
yasincoder doctor
yasincoder models
yasincoder chat "Hello from YasinCoder"
```

The same configuration contract supports `openai_compatible`, `openai`, `custom`, `ollama`, `llama_cpp`, `cloudflare`, and `gemini` provider types. Local models are never bundled. See `docs/CONFIGURATION.md` for the external model registry and provider-specific environment references.

## CLI

Common commands:

```text
help                    Show commands
info                    Show runtime/package information
doctor                  Validate environment and model registry
tui                     Launch the interactive Terminal UI
setup gemini            Configure Gemini API key and set Gemini as the default AI
models                  List configured models without printing credentials
project                 Inspect the current project
search <keyword>        Search project files
read <file>             Read a project file
chat <message>          Send a chat request
review <file>           Review a file
fix <file>              Ask the agent to fix a file
refactor <file>         Refactor a file
explain <file> [q]      Explain a file
autonomous <task>       Run an autonomous coding task
plan <task>             Produce an autonomous plan
testgen [action]        Report/generate/run/verify tests
```

## Gateway

The local gateway binds to `127.0.0.1` by default and exposes OpenAI-compatible health, model, routing, chat, and streaming routes. Protected routes use the configured API key and origin policy. Request bodies and subprocess output are bounded; tool execution rejects shell control operators and enforces workspace confinement.

See `docs/GATEWAY.md` for the contract and `docs/SECURITY.md` for security boundaries.

## Cloudflare Worker

An optional remote gateway is provided under `worker/`. It supports the same health, models, and chat routes, forwards streaming responses to a configured OpenAI-compatible upstream, and keeps client/upstream credentials server-side.

See `worker/README.md` for Wrangler deployment and secret configuration.

## Supported platforms

The Python project declares Python `>=3.10`. CI verifies Python 3.10–3.13 on Linux and runs platform integration coverage on Linux, macOS, and Windows with Python 3.12. Native Termux/Android remains a first-class target but is not executed by repository CI; interactive Android acceptance must be verified on a real Termux environment. Local model runtimes such as Ollama or llama.cpp are external dependencies.

## Security rules

- Never commit API keys, tokens, passwords, certificates, model weights, runtime state, logs, or caches.
- Never put credentials directly into the model registry; reference environment variables or the user-only Gemini credential file instead.
- Keep autonomous execution inside an approved workspace.
- Use explicit permissions for writes, command execution, network, Git, and admin operations.
- Do not expose an unauthenticated local provider directly to a network.
- The TUI must never display secret values.

## Verification

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
```

CI additionally validates repository hygiene, package installation, the Python matrix, wheel creation, and Cloudflare Worker syntax/contract invariants.

## Project documentation

- `docs/ARCHITECTURE.md` — component boundaries and design
- `docs/CONFIGURATION.md` — model registry, Gemini setup, and environment configuration
- `docs/TUI.md` — Terminal UI usage and Termux behavior
- `docs/GATEWAY.md` — local gateway API
- `docs/SECURITY.md` — execution and secret-handling rules
- `docs/RELEASE.md` — versioning and release policy
- `docs/TROUBLESHOOTING.md` — common setup/runtime failures
- `docs/DIAGNOSTICS.md` — bounded production diagnostic categories and redaction rules
- `worker/README.md` — Cloudflare Worker deployment

Roadmap state is tracked by GitHub Issues; completed features should not remain duplicated as TODO items.
