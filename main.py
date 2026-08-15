import sys

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
from commands.autonomous import AutonomousCommand
from commands.testgen import TestGenCommand


def _testgen_args(args):
    action = args[0] if args and not args[0].startswith("-") else "report"
    changed_only = "--changed" in args
    base_ref = "HEAD^"
    timeout = 60
    if "--base" in args:
        index = args.index("--base")
        if index + 1 >= len(args):
            raise SystemExit("Usage: testgen [report|generate|run|verify] [--changed] [--base REF] [--timeout SECONDS]")
        base_ref = args[index + 1]
    if "--timeout" in args:
        index = args.index("--timeout")
        if index + 1 >= len(args):
            raise SystemExit("Usage: testgen [report|generate|run|verify] [--changed] [--base REF] [--timeout SECONDS]")
        timeout = float(args[index + 1])
    return action, changed_only, base_ref, timeout


def main():
    show()
    if len(sys.argv) == 1:
        print(HelpCommand().run())
        return

    cmd = sys.argv[1]
    if cmd == "help":
        print(HelpCommand().run())
    elif cmd == "info":
        print(InfoCommand().run())
    elif cmd == "models":
        print(ModelsCommand().run())
    elif cmd == "doctor":
        from doctor import run as doctor_run
        raise SystemExit(doctor_run())
    elif cmd == "project":
        print(ProjectCommand().run())
    elif cmd == "brain":
        brain = BrainCommand().run()
        print("FILES:", len(brain))
        for item in brain:
            print(item["file"])
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: search keyword")
            return
        for file in SearchCommand().run(sys.argv[2]):
            print(file)
    elif cmd == "read":
        if len(sys.argv) < 3:
            print("Usage: read filename.py")
            return
        print(ReadCommand().run(sys.argv[2]))
    elif cmd == "chat":
        print(ChatCommand().run(" ".join(sys.argv[2:])))
    elif cmd == "review":
        print(ReviewCommand().run(sys.argv[2]))
    elif cmd == "fix":
        print(FixCommand().run(sys.argv[2]))
    elif cmd == "refactor":
        print(RefactorCommand().run(sys.argv[2]))
    elif cmd == "explain":
        filename = sys.argv[2]
        question = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else "Explain this file."
        print(ExplainCommand().run(filename, question))
    elif cmd == "autonomous":
        if len(sys.argv) < 3:
            print("Usage: autonomous <coding task>")
            return
        print(AutonomousCommand().run(" ".join(sys.argv[2:])))
    elif cmd == "plan":
        if len(sys.argv) < 3:
            print("Usage: plan <coding task>")
            return
        print(AutonomousCommand().plan(" ".join(sys.argv[2:])))
    elif cmd == "testgen":
        try:
            action, changed_only, base_ref, timeout = _testgen_args(sys.argv[2:])
            print(TestGenCommand().run(action, changed_only=changed_only, base_ref=base_ref, timeout=timeout))
        except (ValueError, IndexError) as exc:
            raise SystemExit(str(exc))
    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()
