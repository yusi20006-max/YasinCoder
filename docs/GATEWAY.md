# YasinCoder Gateway

The universal gateway is the application boundary between the PWA/clients and configured AI providers.

## Endpoints

### Public health

- `GET /health`
- `GET /api/status`

These endpoints expose only service/routing health and do not require an API key.

### Protected model discovery

- `GET /v1/models`
- `GET /api/models`

### Protected routing diagnostics

- `GET /v1/routing`
- `GET /api/routing`

### Protected chat contract

- `POST /v1/chat/completions`
- `POST /api/chat`

Request body follows the OpenAI-style chat shape:

```json
{
  "model": "auto",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

The gateway returns a provider-neutral `chat.completion` response and includes routing metadata without exposing provider credentials or internal exception details.

## Security

The default server binds to `127.0.0.1`. Protected routes use the runtime API key and allowed-origin policy from `SecurityPolicy`. Request bodies are size-limited and malformed/unknown requests return structured errors.

For a remote deployment, put an authenticated reverse proxy or equivalent access boundary in front of the gateway and configure explicit allowed origins. Do not expose an unauthenticated local provider directly to the network.

## Provider independence

The gateway never assumes a particular model, GGUF file, llama.cpp installation, port, or device path. Local AI is configured by the user through the provider layer; online providers are selected through the same provider-neutral contract.

## Verification

Run the deterministic suite from a clean clone:

```bash
python -m compileall -q .
python -m unittest discover -s tests -p 'test_*.py' -v
```

The clean-clone tests explicitly reject bundled model weights and known Termux developer paths.
