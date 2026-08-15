import sys

from router import Router

from core.banner import show
from commands.git import GitCommand
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
from commands.memory import MemoryCommand
from commands.index import IndexCommand
from commands.stats import StatsCommand
from commands.docs import DocsCommand


def main():
    show()
    if len(sys.argv) < 2:
        HelpCommand().run()
        return
    command = sys.argv[1]
    args = sys.argv[2:]
    if command == "help":
        HelpCommand().run()
    elif command == "info":
        InfoCommand().run()
    elif command == "models":
        ModelsCommand().run()
    elif command == "git":
        GitCommand().run(args)
    elif command == "project":
        ProjectCommand().run()
    elif command == "brain":
        BrainCommand().run()
    elif command == "search":
        SearchCommand().run(args)
    elif command == "read":
        ReadCommand().run(args)
    elif command == "chat":
        ChatCommand().run(args)
    elif command == "explain":
        ExplainCommand().run(args)
    elif command == "fix":
        FixCommand().run(args)
    elif command == "refactor":
        RefactorCommand().run(args)
    elif command == "review":
        ReviewCommand().run(args)
    elif command == "memory":
        MemoryCommand().run(args)
    elif command == "index":
        IndexCommand().run()
    elif command == "stats":
        StatsCommand().run()
    elif command == "docs":
        action = args[0] if args and not args[0].startswith("-") else "all"
        base_ref = "HEAD^"
        output = None
        if "--base" in args:
            i = args.index("--base")
            if i + 1 >= len(args):
                raise SystemExit("Usage: docs [all|api|architecture|report|changes] [--base REF] [--output FILE]")
            base_ref = args[i + 1]
        if "--output" in args:
            i = args.index("--output")
            if i + 1 >= len(args):
                raise SystemExit("Usage: docs [all|api|architecture|report|changes] [--base REF] [--output FILE]")
            output = args[i + 1]
        print(DocsCommand().run(action, base_ref=base_ref, output=output))
    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()
