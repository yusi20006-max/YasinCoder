from providers.base import BaseProvider

class LocalProvider(BaseProvider):

    name="local"

    def chat(self,prompt):

        return "Local model is not configured yet."
