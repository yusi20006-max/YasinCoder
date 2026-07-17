import subprocess


class GitManager:

    def status(self):
        return subprocess.getoutput("git status")

    def diff(self):
        return subprocess.getoutput("git diff")

    def commit_message(self):

        diff = self.diff()

        if not diff.strip():
            return "Nothing to commit."

        return (
            "Suggested Commit Message\n"
            "-------------------------\n"
            "Update project files"
        )
