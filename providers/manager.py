from providers.cloudflare import CloudflareProvider
from providers.local import LocalProvider

class ProviderManager:

    def __init__(self):

        self.providers={

            "cloudflare":CloudflareProvider(),

            "local":LocalProvider()

        }

    def ask(self,prompt):

        return self.providers["cloudflare"].chat(prompt)
