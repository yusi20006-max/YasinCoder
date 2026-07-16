import subprocess


class GitManager:

    def status(self):

        return subprocess.getoutput("git status")


    def diff(self):

        return subprocess.getoutput("git diff")


    def commit_message(self):

        return "feat: update by YasinCoder"
