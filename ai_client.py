from providers.manager import ProviderManager


class AIClient:
    def __init__(self, *args, **kwargs):
        self.provider = ProviderManager()

    def chat(self, prompt, provider=None):
        return self.provider.ask(prompt, provider=provider)
