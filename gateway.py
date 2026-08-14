"""Provider-neutral HTTP gateway for YasinCoder with a static PWA shell."""
from __future__ import annotations

import json
import mimetypes
import time
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from providers.manager import ProviderManager
from routing import RoutingError
from security import DEFAULT_SECURITY_POLICY, SecurityPolicy

WEB_ROOT = Path(__file__).resolve().parent / "web"


class GatewayError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


class Gateway:
    def __init__(self, manager: ProviderManager | None = None):
        self.manager = manager or ProviderManager()

    def models(self) -> list[dict[str, Any]]:
        return [{
            "id": m.get("name") or m.get("model"),
            "name": m.get("name") or m.get("model"),
            "provider": m.get("type", "unknown"),
            "capabilities": m.get("capabilities", ["chat"]),
            "default": m.get("default", False),
        } for m in self.manager.list_models()]

    def routing(self) -> dict[str, Any]:
        return dict(self.manager.last_routing)

    def chat(self, payload: dict[str, Any]) -> dict[str, Any]:
        messages = payload.get("messages")
        if not isinstance(messages, list) or not messages or len(messages) > 128:
            raise GatewayError("invalid_request", "messages must be a non-empty list with at most 128 items")
        text = "\n".join(str(m.get("content", "")) for m in messages if isinstance(m, dict))
        if not text.strip():
            raise GatewayError("invalid_request", "messages contain no text content")
        requested = payload.get("model")
        if requested is not None and (not isinstance(requested, str) or len(requested) > 256):
            raise GatewayError("invalid_request", "model must be a short string")
        model = self.manager.models.get(requested) if requested else self.manager.models.default()
        if requested and not model:
            raise GatewayError("model_not_found", f"Model '{requested}' is not configured", 404)
        try:
            output = self.manager.ask(text, model_name=requested)
        except RoutingError as exc:
            status = 401 if exc.kind == "auth" else 429 if exc.kind == "quota" else 503 if exc.kind in {"timeout", "network", "server"} else 502
            raise GatewayError(f"provider_{exc.kind}", f"Provider routing failed: {exc.kind}", status) from exc
        except Exception as exc:
            raise GatewayError("provider_error", "Configured provider failed", 502) from exc
        return {
            "id": f"yasin-{int(time.time() * 1000)}", "object": "chat.completion",
            "created": int(time.time()), "model": (model or {}).get("name") or requested or "auto",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": str(output)}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}, "routing": self.routing(),
        }


class Handler(BaseHTTPRequestHandler):
    gateway: Gateway | None = None
    security: SecurityPolicy = DEFAULT_SECURITY_POLICY
    server_version = "YasinCoderGateway/1.0"

    def _send(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        for key, value in self.security.public_headers(self.headers.get("Origin")).items():
            self.send_header(key, value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self) -> bool:
        origin = self.headers.get("Origin")
        if not self.security.origin_allowed(origin):
            self._send(403, {"error": {"code": "origin_forbidden", "message": "Origin is not allowed"}})
            return False
        if not self.security.authenticate(self.headers.get("Authorization", "").removeprefix("Bearer ").strip()):
            self._send(401, {"error": {"code": "unauthorized", "message": "Authentication required"}})
            return False
        return True

    def _static(self) -> bool:
        path = self.path.split("?", 1)[0]
        if path in ("/", "/web", "/web/"): path = "/web/index.html"
        if not path.startswith("/web/"): return False
        target = (WEB_ROOT / path.removeprefix("/web/")).resolve()
        if WEB_ROOT not in target.parents and target != WEB_ROOT: return False
        if not target.is_file(): return False
        body = target.read_bytes(); ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        for key, value in self.security.public_headers(self.headers.get("Origin")).items():
            self.send_header(key, value)
        self.send_header("Content-Type", ctype); self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return True

    def do_OPTIONS(self) -> None:
        if not self._authorized(): return
        self.send_response(204)
        for key, value in self.security.public_headers(self.headers.get("Origin")).items():
            self.send_header(key, value)
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        if not self._authorized(): return
        if self._static(): return
        if self.path in ("/health", "/api/status"):
            self._send(200, {"ok": True, "service": "yasin-coder-gateway", "routing": self.gateway.routing()}); return
        if self.path in ("/api/routing", "/v1/routing"):
            self._send(200, {"ok": True, "routing": self.gateway.routing()}); return
        if self.path in ("/v1/models", "/api/models"):
            try: self._send(200, {"object": "list", "data": self.gateway.models()})
            except Exception: self._send(500, {"error": {"code": "internal_error", "message": "Unable to list models"}})
            return
        self._send(404, {"error": {"code": "not_found", "message": "Route not found"}})

    def do_POST(self) -> None:
        if not self._authorized(): return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > self.security.max_body_bytes:
                self._send(413, {"error": {"code": "payload_too_large", "message": "Request body is too large"}}); return
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                self._send(400, {"error": {"code": "invalid_json", "message": "Request body must be a JSON object"}}); return
        except (ValueError, json.JSONDecodeError):
            self._send(400, {"error": {"code": "invalid_json", "message": "Request body must be JSON"}}); return
        if self.path in ("/v1/chat/completions", "/api/chat"):
            try: self._send(200, self.gateway.chat(payload))
            except GatewayError as exc: self._send(exc.status, {"error": {"code": exc.code, "message": exc.message}})
            except Exception: self._send(500, {"error": {"code": "internal_error", "message": "Gateway request failed"}})
            return
        self._send(404, {"error": {"code": "not_found", "message": "Route not found"}})

    def log_message(self, format: str, *args: Any) -> None: return


def create_server(host: str = "127.0.0.1", port: int = 18765, manager: ProviderManager | None = None,
                  security: SecurityPolicy | None = None):
    Handler.gateway = Gateway(manager)
    Handler.security = security or SecurityPolicy.from_env()
    return ThreadingHTTPServer((host, port), Handler)


def main() -> None:
    server = create_server(); print(f"YasinCoder gateway listening on http://{server.server_address[0]}:{server.server_address[1]}"); server.serve_forever()


if __name__ == "__main__": main()
