class Context:

    def __init__(self):

        self.project=None

        self.file=None

        self.command=None

        self.question=None

    def dump(self):

        return {

            "project":self.project,

            "file":self.file,

            "command":self.command,

            "question":self.question

        }
