from models.manager import ModelManager
from providers.cloudflare import CloudflareProvider
from providers.model_endpoint import ModelEndpoint
from config import MODEL, CF_ACCOUNT_ID, CF_API_TOKEN


class ProviderManager:
    """Select configured providers without embedding machine-specific models."""

    def __init__(self):
        self.models = ModelManager()
        self.models.ensure_discovered()
        self.providers = {"cloudflare": CloudflareProvider()}

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

    def ask(self, prompt):
        selected = MODEL.strip() if MODEL.strip() and MODEL.strip() != "auto" else None
        model = self.models.get(selected) if selected else self.models.default()

        if model and model.get("type") in {"llama_cpp", "ollama", "openai_compatible"}:
            endpoint = ModelEndpoint(model)
            if not endpoint.health():
                return f"Model '{model.get('name')}' is unavailable; configure another model."
            return endpoint.chat(prompt)

        if model and model.get("type") == "cloudflare":
            return self.providers["cloudflare"].chat(prompt)

        if CF_ACCOUNT_ID and CF_API_TOKEN:
            return self.providers["cloudflare"].chat(prompt)
        return "No AI model configured. Run model setup or set YASIN_BASE_URL/YASIN_MODEL_NAME."
