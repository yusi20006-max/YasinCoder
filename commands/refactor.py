from agent import YasinAgent

class RefactorCommand:

    def run(self,filename):

        agent=YasinAgent()

        return agent.analyze(

            filename,

            "Refactor this file. Improve readability and performance without changing behaviour."

        )
