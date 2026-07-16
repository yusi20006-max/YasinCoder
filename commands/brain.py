from config import PROJECT_PATH
from core.project_brain import ProjectBrain

class BrainCommand:

    def run(self):

        brain=ProjectBrain()

        return brain.build(PROJECT_PATH)
