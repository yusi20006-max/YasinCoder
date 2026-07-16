class ModelSelector:

    def choose(self,task):

        task=task.lower()

        if "review" in task:

            return "deepseek-chat"

        if "fix" in task:

            return "deepseek-chat"

        return "auto"
