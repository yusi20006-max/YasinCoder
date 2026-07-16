from agent import YasinAgent

class FixCommand:

    def run(self,filename):

        agent=YasinAgent()

        return agent.analyze(

            filename,

            "Fix every bug. Keep compatibility. Return complete code."

        )
