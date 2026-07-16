from ai_client import AIClient

class ChatCommand:

    def run(self,prompt):

        client=AIClient()

        return client.chat(prompt)
