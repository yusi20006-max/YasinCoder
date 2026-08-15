class HelpCommand:
    def run(self):
        return """

YasinCoder Commands

help
info
models
project
brain
search
read
chat [prompt]
chat --interactive
chat --resume SESSION_ID
chat --list-sessions
chat --delete-session SESSION_ID
review
fix
refactor
explain
doctor

Interactive chat commands: /exit, /quit, /sessions, /provider NAME, /model NAME, /clear
"""
