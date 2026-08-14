import os

from providers.cloudflare import CloudflareProvider
from providers.local import LocalProvider


class ProviderManager:
    """Registry and selector for configured AI providers."""

    def __init__(self, default=None):
        self.providers = {
            "cloudflare": CloudflareProvider(),
            "local": LocalProvider(),
        }
        self.default = default or os.getenv("YASIN_AI_PROVIDER", "cloudflare")
        if self.default not in self.providers:
            raise ValueError(f"Unsupported AI provider: {self.default}")

    def get(self, name=None):
        provider_name = name or self.default
        try:
            return self.providers[provider_name]
        except KeyError as exc:
            raise ValueError(f"Unsupported AI provider: {provider_name}") from exc

    def ask(self, prompt, provider=None):
        return self.get(provider).chat(prompt)

    def health(self, provider=None):
        return self.get(provider).health()

    def capabilities(self, provider=None):
        return self.get(provider).capabilities()
