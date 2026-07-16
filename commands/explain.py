from agent import YasinAgent

class ExplainCommand:

    def run(self,filename,question):

        agent=YasinAgent()

        return agent.analyze(filename,question)
