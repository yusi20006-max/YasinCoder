from project import read_file
from providers.manager import ProviderManager

class YasinAgent:

    def __init__(self):

        self.ai=ProviderManager()

    def analyze(self,filename,instruction):

        code=read_file(filename)

        prompt=f"""

You are an expert software engineer.

Instruction:

{instruction}

File:

{filename}

Source Code:

{code}

"""

        return self.ai.ask(prompt)
