from agent import YasinAgent

class ReviewCommand:

    def run(self,filename):

        agent=YasinAgent()

        return agent.analyze(

            filename,

            "Review this code. Find bugs, security issues, bad practices and improvements."

        )
