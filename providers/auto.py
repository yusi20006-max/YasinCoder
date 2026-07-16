from providers.manager import ProviderManager

class AutoProvider:

    def __init__(self):

        self.manager=ProviderManager()

    def ask(self,prompt):

        try:

            return self.manager.ask(prompt)

        except Exception as e:

            return "Provider error: "+str(e)
