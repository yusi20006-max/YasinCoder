"""Provider-neutral HTTP gateway for YasinCoder with streaming support."""
from __future__ import annotations
import json, mimetypes, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
from core.gateway_contract import chat_response, error_response, validate_chat_request
from providers.manager import ProviderManager
from routing import RoutingError
from security import DEFAULT_SECURITY_POLICY, SecurityPolicy
WEB_ROOT = Path(__file__).resolve().parent / "web"

class GatewayError(Exception):
    def __init__(self, code: str, message: str, status: int = 400): super().__init__(message); self.code, self.message, self.status = code, message, status

class Gateway:
    def __init__(self, manager: ProviderManager | None = None): self.manager = manager or ProviderManager()
    def models(self) -> list[dict[str, Any]]:
        return [{"id": m.get("name") or m.get("model"), "name": m.get("name") or m.get("model"), "provider": m.get("type", "unknown"), "capabilities": m.get("capabilities", ["chat"]), "default": m.get("default", False)} for m in self.manager.list_models()]
    def routing(self): return dict(self.manager.last_routing)
    def _text(self, payload):
        try: requested, messages = validate_chat_request(payload)
        except ValueError as exc: raise GatewayError("invalid_request", str(exc)) from exc
        text = "\n".join(str(m.get("content", "")) for m in messages if isinstance(m, dict))
        if not text.strip(): raise GatewayError("invalid_request", "messages contain no text content")
        model = self.manager.models.get(requested) if requested else self.manager.models.default()
        if requested and not model: raise GatewayError("model_not_found", f"Model '{requested}' is not configured", 404)
        return requested, text, model
    def chat(self, payload):
        requested, text, model = self._text(payload)
        try: output = self.manager.ask(text, model_name=requested)
        except RoutingError as exc:
            status = {"auth": 401, "quota": 429, "rate_limit": 429, "timeout": 503, "network": 503, "server": 503}.get(exc.kind, 502)
            raise GatewayError(f"provider_{exc.kind}", f"Provider routing failed: {exc.kind}", status) from exc
        except Exception as exc: raise GatewayError("provider_error", "Configured provider failed", 502) from exc
        return chat_response(request_id=f"yasin-{int(time.time() * 1000)}", model=(model or {}).get("name") or requested or "auto", content=str(output), created=int(time.time()), routing=self.routing())
    def stream(self, payload) -> Iterator[dict[str, Any]]:
        requested, text, model = self._text(payload)
        model_name = (model or {}).get("name") or requested or "auto"
        created = int(time.time()); request_id = f"yasin-{int(time.time() * 1000)}"
        try:
            for selected, chunk in self.manager.stream(text, model_name=requested):
                yield {"id": request_id, "object": "chat.completion.chunk", "created": created, "model": selected or model_name, "choices": [{"index": 0, "delta": {"content": chunk}, "finish_reason": None}]}
            yield {"id": request_id, "object": "chat.completion.chunk", "created": created, "model": self.manager.routing().get("selected") or model_name, "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}
        except RoutingError as exc:
            status = {"auth": 401, "quota": 429, "rate_limit": 429, "timeout": 503, "network": 503, "server": 503}.get(exc.kind, 502)
            raise GatewayError(f"provider_{exc.kind}", f"Provider routing failed: {exc.kind}", status) from exc
        except Exception as exc: raise GatewayError("provider_error", "Configured provider failed", 502) from exc

class Handler(BaseHTTPRequestHandler):
    gateway: Gateway | None = None
    security: SecurityPolicy = DEFAULT_SECURITY_POLICY
    server_version = "YasinCoderGateway/1.0"
    def _send(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode(); self.send_response(status)
        for key, value in self.security.public_headers(self.headers.get("Origin")).items(): self.send_header(key, value)
        self.send_header("Content-Type", "application/json; charset=utf-8"); self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def _origin_allowed(self):
        if self.security.origin_allowed(self.headers.get("Origin")): return True
        self._send(403, error_response("origin_forbidden", "Origin is not allowed")); return False
    def _authorized(self):
        if not self._origin_allowed(): return False
        token = self.headers.get("Authorization", "").removeprefix("Bearer ").strip()
        if not self.security.authenticate(token): self._send(401, error_response("unauthorized", "Authentication required")); return False
        return True
    def _static(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/web", "/web/"): path = "/web/index.html"
        if not path.startswith("/web/"): return False
        target = (WEB_ROOT / path.removeprefix("/web/")).resolve()
        if WEB_ROOT not in target.parents and target != WEB_ROOT or not target.is_file(): return False
        body = target.read_bytes(); ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"; self.send_response(200)
        for key, value in self.security.public_headers(self.headers.get("Origin")).items(): self.send_header(key, value)
        self.send_header("Content-Type", ctype); self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return True
    def do_OPTIONS(self):
        if not self._origin_allowed(): return
        self.send_response(204)
        for key, value in self.security.public_headers(self.headers.get("Origin")).items(): self.send_header(key, value)
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type"); self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS"); self.send_header("Access-Control-Max-Age", "600"); self.end_headers()
    def do_GET(self):
        if self._static(): return
        if self.path in ("/health", "/api/status"):
            if not self._origin_allowed(): return
            self._send(200, {"ok": True, "service": "yasin-coder-gateway", "routing": self.gateway.routing()}); return
        if not self._authorized(): return
        if self.path in ("/api/routing", "/v1/routing"): self._send(200, {"ok": True, "routing": self.gateway.routing()}); return
        if self.path in ("/v1/models", "/api/models"):
            try: self._send(200, {"object": "list", "data": self.gateway.models()})
            except Exception: self._send(500, error_response("internal_error", "Unable to list models"))
            return
        self._send(404, error_response("not_found", "Route not found"))
    def do_POST(self):
        if not self._authorized(): return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > self.security.max_body_bytes: self._send(413, error_response("payload_too_large", "Request body is too large")); return
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict): self._send(400, error_response("invalid_json", "Request body must be a JSON object")); return
        except (ValueError, json.JSONDecodeError): self._send(400, error_response("invalid_json", "Request body must be JSON")); return
        if self.path not in ("/v1/chat/completions", "/api/chat"): self._send(404, error_response("not_found", "Route not found")); return
        if payload.get("stream") is True:
            try:
                self.send_response(200)
                for key, value in self.security.public_headers(self.headers.get("Origin")).items(): self.send_header(key, value)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8"); self.send_header("Cache-Control", "no-cache, no-store"); self.send_header("Connection", "keep-alive"); self.end_headers()
                for event in self.gateway.stream(payload):
                    self.wfile.write(("data: " + json.dumps(event, ensure_ascii=False) + "\n\n").encode()); self.wfile.flush()
                self.wfile.write(b"data: [DONE]\n\n"); self.wfile.flush()
            except GatewayError as exc:
                try: self.wfile.write(("data: " + json.dumps(error_response(exc.code, exc.message)) + "\n\n").encode()); self.wfile.flush()
                except OSError: pass
            except (BrokenPipeError, ConnectionResetError): pass
            return
        try: self._send(200, self.gateway.chat(payload))
        except GatewayError as exc: self._send(exc.status, error_response(exc.code, exc.message))
        except Exception: self._send(500, error_response("internal_error", "Gateway request failed"))
    def log_message(self, format: str, *args: Any): return

def create_server(host="127.0.0.1", port=18765, manager=None, security=None):
    Handler.gateway = Gateway(manager); Handler.security = security or SecurityPolicy.from_env(); return ThreadingHTTPServer((host, port), Handler)

def main():
    server = create_server(); print(f"YasinCoder gateway listening on http://{server.server_address[0]}:{server.server_address[1]}"); server.serve_forever()

if __name__ == "__main__": main()
