"""Provider registry and adapter orchestration."""
from __future__ import annotations
from typing import Iterator
from config import CF_ACCOUNT_ID, CF_API_TOKEN, CF_MODEL, MODEL
from models.manager import ModelManager
from routing import Router, RoutingError, TRANSIENT, classify_error
from .base import ProviderError, ProviderUnavailable
from .factory import create_adapter

class ProviderManager:
    """Select configured models while keeping gateway code provider-neutral."""
    def __init__(self):
        self.models = ModelManager(); self.models.ensure_discovered()
        self.last_routing = {"selected": None, "attempts": [], "offline": False}
    def list_models(self): return self.models.list()
    def register(self, model): return self.models.upsert(model)
    def remove(self, name): return self.models.remove(name)
    def select(self, name): return self.models.select(name)
    def _configured_models(self):
        models = {m.get("name"): m for m in self.models.list() if m.get("name")}
        if CF_ACCOUNT_ID and CF_API_TOKEN and CF_MODEL and "cloudflare" not in models:
            models["cloudflare"] = {"name": "cloudflare", "type": "cloudflare", "model": CF_MODEL, "account_id": CF_ACCOUNT_ID, "api_token": CF_API_TOKEN}
        return models
    def _adapter(self, model): return create_adapter(ModelManager.resolve_secrets(model))
    def health(self, name=None):
        model = self.models.get(name) if name else self.models.default()
        if not model: return False
        try: return self._adapter(model).health()
        except ProviderError: return False
    def routing(self): return dict(self.last_routing)
    def _ask_model(self, model, prompt):
        adapter = self._adapter(model)
        if not adapter.health(): raise ProviderUnavailable("provider is unavailable")
        return adapter.chat(prompt)
    def _stream_model(self, model, prompt) -> Iterator[str]:
        adapter = self._adapter(model)
        if not adapter.health(): raise ProviderUnavailable("provider is unavailable")
        yield from adapter.stream_chat(prompt)
    def _primary(self, model_name=None):
        selected = model_name or (MODEL.strip() if MODEL.strip() and MODEL.strip() != "auto" else None)
        return self.models.get(selected) if selected else self.models.default()
    def ask(self, prompt, model_name=None):
        primary = self._primary(model_name)
        if not primary:
            self.last_routing = {"selected": None, "attempts": [], "offline": False, "error": "configuration"}; return "No AI model configured. Configure a local or online provider first."
        offline = bool(primary.get("offline", False)); resolver_models = self._configured_models(); router = Router(lambda name: resolver_models.get(name) or self.models.get(name))
        try: result = router.run(primary, lambda model: self._ask_model(model, prompt))
        except RoutingError as exc:
            self.last_routing = {"selected": None, "attempts": [a.__dict__ for a in exc.attempts], "offline": offline, "error": exc.kind}; raise
        self.last_routing = {"selected": result.selected, "attempts": [a.__dict__ for a in result.attempts], "offline": offline}; return result.output
    def stream(self, prompt: str, model_name=None) -> Iterator[tuple[str, str]]:
        primary = self._primary(model_name)
        if not primary:
            self.last_routing = {"selected": None, "attempts": [], "offline": False, "error": "configuration"}; raise RoutingError("configuration", "No AI model configured")
        offline = bool(primary.get("offline", False)); resolver_models = self._configured_models(); router = Router(lambda name: resolver_models.get(name) or self.models.get(name))
        chain = [primary] if primary.get("offline") is True else router.order(primary)
        attempts = []
        for model in chain:
            name = str(model.get("name") or model.get("model") or "unknown")[:128].replace("\n", " ").replace("\r", " "); emitted = False
            try:
                for chunk in self._stream_model(model, prompt):
                    if chunk:
                        emitted = True; self.last_routing = {"selected": name, "attempts": attempts + [{"model": name, "outcome": "streaming"}], "offline": offline}; yield name, str(chunk)
                attempts.append({"model": name, "outcome": "success"}); self.last_routing = {"selected": name, "attempts": attempts, "offline": offline}; return
            except Exception as exc:
                kind = classify_error(exc); attempts.append({"model": name, "outcome": kind, "error": kind})
                if emitted or kind not in TRANSIENT:
                    self.last_routing = {"selected": None, "attempts": attempts, "offline": offline, "error": kind}; raise RoutingError(kind, f"Provider '{name}' failed: {kind}", [type("Attempt", (), a)() for a in attempts]) from exc
        kind = attempts[-1]["outcome"] if attempts else "configuration"; self.last_routing = {"selected": None, "attempts": attempts, "offline": offline, "error": kind}; raise RoutingError(kind, "No provider succeeded")
