class Session:

    def __init__(self):

        self.project=None

        self.file=None

        self.provider=None

        self.model=None

    def to_dict(self):

        return {

            "project":self.project,

            "file":self.file,

            "provider":self.provider,

            "model":self.model

        }
