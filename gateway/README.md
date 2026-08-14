# YasinCoder Gateway

This directory is the destination for the working local AI gateway currently running as the standalone `gemini-web` application.

## Migration contract

The migration must preserve these verified behaviors before refactoring:

- `GET /api/status`
- `GET /api/logs`
- `POST /api/start`
- `POST /api/stop`
- `POST /api/restart`
- `POST /api/qwen`
- `POST /api/gemini`
- web UI on port `18765`
- local Qwen runtime on port `18080`
- Gemini CLI detection
- start/stop/restart lifecycle

## Runtime rules

- Default bind: `127.0.0.1`.
- Qwen process management stays inside the gateway.
- Do not expose the Qwen port directly to untrusted networks.
- Do not commit credentials.
- Preserve a backup before migration and keep a parity test against the known-good standalone gateway.

The implementation files are migrated only after the source `gemini-web` files are available to the repository workflow; this avoids recreating or silently changing working code from partial logs.
