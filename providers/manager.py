from providers.cloudflare import CloudflareProvider
from providers.local import LocalProvider
from config import MODEL, CF_ACCOUNT_ID, CF_API_TOKEN

class ProviderManager:

    def __init__(self):

        self.providers={
            "cloudflare":CloudflareProvider(),
            "local":LocalProvider()
        }

    def ask(self,prompt):

        provider=MODEL

        if provider=="auto":
            # auto: use Cloudflare if configured, otherwise fall back
            # to the local provider instead of failing outright.
            if CF_ACCOUNT_ID and CF_API_TOKEN:
                provider="cloudflare"
            else:
                provider="local"

        if provider not in self.providers:
            return f"Unknown provider '{provider}' (check MODEL in config.py)"

        return self.providers[provider].chat(prompt)
