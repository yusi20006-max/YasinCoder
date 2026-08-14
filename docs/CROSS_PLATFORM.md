# Cross-platform runtime support

YasinCoder keeps OS-specific behavior behind `core.runtime` so provider and agent code can run without assuming Termux, Linux, macOS, Windows, or a particular shell.

## Supported targets

- Android / Termux
- Linux
- Ubuntu / Debian
- macOS
- Windows
- Windows Subsystem for Linux (WSL)

The runtime detector exposes a normalized `RuntimeInfo.family` value and flags for Termux and WSL.

## Runtime data and configuration

User data, configuration, and cache locations are derived from native conventions:

- Linux/WSL/Termux: XDG variables when supplied, otherwise `~/.local/share`, `~/.config`, and `~/.cache`.
- macOS: `~/Library/Application Support`, `~/Library/Preferences`, and `~/Library/Caches`.
- Windows: `%APPDATA%` / `%LOCALAPPDATA%` with safe home-directory fallbacks.

No developer-specific absolute paths are required.

## External runtimes

Executables such as llama.cpp, Ollama, Git, and provider CLIs must be discovered through `PATH` or explicit user configuration. Use `find_command()` / `command_available()` instead of hard-coded Termux paths.

Processes are launched with argument arrays and `shell=False`; shell-specific quoting is therefore not part of the core runtime contract.

## Local model portability

YasinCoder does not bundle or assume a GGUF file. A user may configure any compatible local model/runtime supported by the provider adapter. The runtime layer only discovers the executable; model paths and model identifiers remain user-owned configuration.

## Verification

Run:

```bash
python -m pytest tests/test_runtime.py
```

The test suite validates runtime detection, native user directories, executable discovery, direct process execution, and graceful handling of missing commands.
