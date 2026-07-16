from providers.manager import ProviderManager

class AIClient:

    def __init__(self,*args,**kwargs):

        self.provider=ProviderManager()

    def chat(self,prompt):

        return self.provider.ask(prompt)
