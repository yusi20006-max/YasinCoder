# YasinCoder Architecture

Status: **Phase 2 — Local AI integration verified**

Repository: `yusi20006-max/YasinCoder`
Default branch: `master`

## Mission
YasinCoder is the canonical Yasin coding-agent application repository. It owns the coding-agent experience, project intelligence, code operations, model selection, and provider integration contracts.

## Target system boundary

```text
                         YasinCoder
                              │
             ┌────────────────┼────────────────┐
             │                │                │
        Agent Core       Project Brain      Commands
             │                │                │
             └────────────────┼────────────────┘
                              │
                        AI Provider Layer
                              │
                ┌─────────────┴─────────────┐
                │                           │
          Local AI Gateway             Cloud AI
                │                           │
          ┌─────┴─────┐              Gemini / other
          │           │
       Qwen local   Gemini CLI
       llama.cpp
          │
     127.0.0.1:18080
          ▲
          │
   Web Control/UI
   127.0.0.1:18765
```

## Current verified runtime

| Component | Address / command | State |
|---|---|---|
| Web gateway | `127.0.0.1:18765` | HTTP 200 verified |
| Python server | `server.py` | running |
| Qwen server | `127.0.0.1:18080` | healthy |
| Model | `Qwen3-1.7B-Q4_K_M.gguf` | loaded |
| Alias | `qwen3-local` | verified |
| Context | 4096 | verified |
| Gemini CLI | `/data/data/com.termux/files/usr/bin/gemini` | executable |
| ripgrep | Termux `rg` 15.2.0 | installed |

## Gateway responsibilities

Read:
- `/api/status` — aggregate gateway, Qwen, Gemini and startup state.
- `/api/logs` — recent Qwen/gateway/startup logs.

Control:
- `/api/start`
- `/api/stop`
- `/api/restart`

AI:
- `/api/qwen`
- `/api/gemini`

Process control must remain separate from provider logic so additional local/cloud providers can be added without rewriting the UI.

## Local Qwen path

```text
Browser → server.py :18765 → llama-server :18080 → Qwen3 1.7B Q4_K_M
```

Observed metadata: about 2.03B parameters, about 1.276 GB GGUF, Q4_K Medium, configured context 4096, 4 slots. The model is a replaceable infrastructure component rather than part of the agent core.

## Gemini path

Gemini is an external CLI provider. The 2026-08-14 audit verified that the CLI exists and is callable, but the configured `gemini-3.5-flash` account exhausted its daily free-tier quota and returned HTTP 429. Therefore Gemini availability is verified, successful generation at audit time is not, and Qwen is the verified offline fallback.

## Lifecycle

```text
START → ensure Qwen → health check → check Gemini → ensure gateway → SYSTEM_READY
STOP  → stop Qwen/system
RESTART → STOP → START
```

The lifecycle was exercised through shell scripts and HTTP control routes.

## Security boundary

Qwen binds to `127.0.0.1`, limiting exposure to the device. llama.cpp currently reports CORS `*` and no API key. This is acceptable only for localhost development. Before remote exposure, add authentication, restrictive CORS, rate/request limits, command allowlisting, audit logging, secret isolation, and safe PID/process ownership.

## Known issues from Phase 1/2

1. Route scan shows duplicate `/api/start` and `/api/stop` branches; clean these during the next code audit.
2. Gemini CLI still emitted a `Ripgrep is not available` fallback message after Termux `rg` 15.2.0 was installed. Investigate the CLI environment/path; this does not block Qwen.
3. Normalize Gemini quota failures into a provider state such as `quota_exhausted`.
4. Evaluate larger local models only after measuring device RAM, thermal behavior and latency.

## Architectural rule

YasinCoder owns the coding-agent application and provider orchestration contract. Local model servers and external CLIs are replaceable infrastructure. The UI must consume stable gateway JSON contracts instead of depending directly on llama.cpp or Gemini CLI details.
