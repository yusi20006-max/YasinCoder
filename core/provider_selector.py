class ProviderSelector:

    def choose(self,task):

        task=task.lower()

        if "review" in task:

            return "deepseek"

        if "fix" in task:

            return "deepseek"

        if "chat" in task:

            return "auto"

        return "auto"
