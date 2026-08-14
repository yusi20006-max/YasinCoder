"""Provider-neutral HTTP gateway for YasinCoder.

The gateway exposes one stable contract for configured AI backends. Runtime/model
configuration remains outside Git and is resolved by ProviderManager.
"""
from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from providers.manager import ProviderManager


class GatewayError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class Gateway:
    def __init__(self, manager: ProviderManager | None = None):
        self.manager = manager or ProviderManager()

    def models(self) -> list[dict[str, Any]]:
        result = []
        for model in self.manager.list_models():
            result.append({
                "id": model.get("name") or model.get("model"),
                "name": model.get("name") or model.get("model"),
                "provider": model.get("type", "unknown"),
                "capabilities": model.get("capabilities", ["chat"]),
                "default": model.get("default", False),
            })
        return result

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages:
            raise GatewayError("invalid_request", "messages must be a non-empty list")

        text_parts = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            content = message.get("content", "")
            if isinstance(content, str) and content:
                text_parts.append(content)
        if not text_parts:
            raise GatewayError("invalid_request", "messages contain no text content")

        prompt = "\n".join(text_parts)
        requested = payload.get("model")
        model = self.manager.models.get(requested) if requested else self.manager.models.default()
        if requested and not model:
            raise GatewayError("model_not_found", f"Model '{requested}' is not configured", 404)

        try:
            output = self.manager.ask(prompt)
        except Exception as exc:
            raise GatewayError("provider_error", str(exc), 502) from exc

        model_name = (model or {}).get("name") or (model or {}).get("model") or requested or "auto"
        return {
            "id": f"yasin-{int(time.time() * 1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model_name,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": str(output)},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }


class Handler(BaseHTTPRequestHandler):
    gateway: Gateway | None = None
    server_version = "YasinCoderGateway/1.0"

    def _send(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/health", "/api/status"):
            self._send(200, {"ok": True, "service": "yasin-coder-gateway"})
            return
        if self.path in ("/v1/models", "/api/models"):
            try:
                models = self.gateway.models()  # type: ignore[union-attr]
                self._send(200, {"object": "list", "data": models})
            except Exception as exc:
                self._send(500, {"error": {"code": "internal_error", "message": str(exc)}})
            return
        self._send(404, {"error": {"code": "not_found", "message": "Route not found"}})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": {"code": "invalid_json", "message": "Request body must be JSON"}})
            return

        if self.path in ("/v1/chat/completions", "/api/chat"):
            try:
                result = self.gateway.chat(payload)  # type: ignore[union-attr]
                self._send(200, result)
            except GatewayError as exc:
                self._send(exc.status, {"error": {"code": exc.code, "message": exc.message}})
            except Exception as exc:
                self._send(500, {"error": {"code": "internal_error", "message": str(exc)}})
            return
        self._send(404, {"error": {"code": "not_found", "message": "Route not found"}})

    def log_message(self, format: str, *args: Any) -> None:
        return


def create_server(host: str = "127.0.0.1", port: int = 18765, manager: ProviderManager | None = None):
    Handler.gateway = Gateway(manager)
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    server = create_server()
    print(f"YasinCoder gateway listening on http://{server.server_address[0]}:{server.server_address[1]}")
    server.serve_forever()


if __name__ == "__main__":
    main()
