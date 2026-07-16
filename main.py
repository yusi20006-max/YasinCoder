import sys

from router import Router

from core.banner import show

from commands.help import HelpCommand
from commands.info import InfoCommand
from commands.models import ModelsCommand
from commands.project import ProjectCommand
from commands.brain import BrainCommand
from commands.search import SearchCommand
from commands.read import ReadCommand
from commands.chat import ChatCommand
from commands.review import ReviewCommand
from commands.fix import FixCommand
from commands.refactor import RefactorCommand
from commands.explain import ExplainCommand

def main():

    show()

    if len(sys.argv)==1:

        print(HelpCommand().run())

        return

    cmd=sys.argv[1]

    if cmd=="help":

        print(HelpCommand().run())

    elif cmd=="info":

        print(InfoCommand().run())

    elif cmd=="models":

        print(ModelsCommand().run())

    elif cmd=="project":

        print(ProjectCommand().run())

    elif cmd=="brain":

        brain=BrainCommand().run()

        print("FILES:",len(brain))

        for item in brain:

            print(item["file"])

    elif cmd=="search":

        if len(sys.argv)<3:

            print("Usage: search keyword")

            return

        result=SearchCommand().run(sys.argv[2])

        for file in result:

            print(file)

    elif cmd=="read":

        if len(sys.argv)<3:

            print("Usage: read filename.py")

            return

        print(ReadCommand().run(sys.argv[2]))

    elif cmd=="chat":

        prompt=" ".join(sys.argv[2:])

        print(ChatCommand().run(prompt))

    elif cmd=="review":

        print(ReviewCommand().run(sys.argv[2]))

    elif cmd=="fix":

        print(FixCommand().run(sys.argv[2]))

    elif cmd=="refactor":

        print(RefactorCommand().run(sys.argv[2]))

    elif cmd=="explain":

        filename=sys.argv[2]

        question="Explain this file."

        if len(sys.argv)>3:

            question=" ".join(sys.argv[3:])

        print(ExplainCommand().run(filename,question))

    else:

        print("Unknown command.")

if __name__=="__main__":

    main()
