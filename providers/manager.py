from models.manager import ModelManager
from providers.cloudflare import CloudflareProvider
from providers.model_endpoint import ModelEndpoint
from config import MODEL, CF_ACCOUNT_ID, CF_API_TOKEN
from routing import Router, RoutingError


class ProviderManager:
    """Select configured providers with deterministic, loop-free fallback."""

    def __init__(self):
        self.models = ModelManager()
        self.models.ensure_discovered()
        self.providers = {"cloudflare": CloudflareProvider()}
        self.last_routing = {"selected": None, "attempts": [], "offline": False}

    def list_models(self):
        return self.models.list()

    def register(self, model):
        return self.models.upsert(model)

    def remove(self, name):
        return self.models.remove(name)

    def select(self, name):
        return self.models.select(name)

    def health(self, name=None):
        model = self.models.get(name) if name else self.models.default()
        if not model:
            return False
        if model.get("type") == "cloudflare":
            return bool(CF_ACCOUNT_ID and CF_API_TOKEN)
        return ModelEndpoint(model).health()

    def _configured_models(self):
        models = {m.get("name"): m for m in self.models.list() if m.get("name")}
        if CF_ACCOUNT_ID and CF_API_TOKEN and "cloudflare" not in models:
            models["cloudflare"] = {"name": "cloudflare", "type": "cloudflare"}
        return models

    def _ask_model(self, model, prompt):
        kind = model.get("type")
        if kind in {"llama_cpp", "ollama", "openai_compatible"}:
            endpoint = ModelEndpoint(model)
            if not endpoint.health():
                raise ConnectionError("provider unavailable")
            return endpoint.chat(prompt)
        if kind == "cloudflare":
            return self.providers["cloudflare"].chat(prompt)
        raise ValueError("unsupported provider type")

    def ask(self, prompt):
        selected = MODEL.strip() if MODEL.strip() and MODEL.strip() != "auto" else None
        primary = self.models.get(selected) if selected else self.models.default()
        if not primary:
            self.last_routing = {"selected": None, "attempts": [], "offline": False}
            return "No AI model configured. Run model setup or set YASIN_BASE_URL/YASIN_MODEL_NAME."

        # Offline mode is explicit and never consults cloud providers.
        offline = bool(primary.get("offline", False))
        if offline and primary.get("type") == "cloudflare":
            raise RoutingError("configuration", "Offline mode cannot use a cloud provider")

        resolver_models = self._configured_models()
        router = Router(lambda name: resolver_models.get(name) or self.models.get(name))
        try:
            result = router.run(primary, lambda model: self._ask_model(model, prompt))
        except RoutingError as exc:
            self.last_routing = {
                "selected": None,
                "attempts": [a.__dict__ for a in getattr(exc, "attempts", [])],
                "offline": offline,
                "error": exc.kind,
            }
            raise

        self.last_routing = {
            "selected": result.selected,
            "attempts": [a.__dict__ for a in result.attempts],
            "offline": offline,
        }
        return result.output
