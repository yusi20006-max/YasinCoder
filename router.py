class Router:

    def parse(self, cmd):

        routes = {

            "help":"help",

            "info":"info",

            "models":"models",

            "project":"project",

            "brain":"brain",

            "search":"search",

            "read":"read",

            "chat":"chat",

            "review":"review",

            "fix":"fix",

            "refactor":"refactor",

            "explain":"explain",

            "index":"index",

            "stats":"stats"

        }

        return routes.get(cmd)
