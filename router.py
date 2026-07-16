class Router:

    def parse(self,args):

        if len(args)<2:

            return None

        cmd=args[1]

        if cmd=="explain":

            if len(args)<3:

                return None

            question="Explain this file."

            if len(args)>3:

                question=" ".join(args[3:])

            return {

                "command":"explain",

                "target":args[2],

                "question":question

            }

        return {

            "command":cmd

        }
