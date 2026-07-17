from git_manager import GitManager


class GitCommand:

    def run(self, args):

        if not args:
            print("Usage:")
            print("  git status")
            print("  git diff")
            print("  git commit")
            return

        git = GitManager()

        cmd = args[0]

        if cmd == "status":
            print(git.status())

        elif cmd == "diff":
            print(git.diff())

        elif cmd == "commit":
            print(git.commit_message())

        else:
            print("Unknown git command.")
