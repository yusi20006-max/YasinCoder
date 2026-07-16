import os

PROMPT_DIR="prompts"

class PromptLoader:

    def load(self,name):

        path=os.path.join(PROMPT_DIR,name+".txt")

        if not os.path.exists(path):

            return ""

        with open(path,"r",encoding="utf8") as f:

            return f.read()
