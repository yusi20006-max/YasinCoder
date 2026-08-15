"""Interactive chat command with persistent resumable sessions."""
from __future__ import annotations

import argparse

from ai_client import AIClient
from core.session import SessionManager


class ChatCommand:
    def __init__(self, sessions: SessionManager | None = None, client: AIClient | None = None):
        self.sessions = sessions or SessionManager()
        self.client = client or AIClient()

    def _parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(prog="yasin-coder chat", add_help=False)
        parser.add_argument("prompt", nargs="*")
        parser.add_argument("--interactive", "-i", action="store_true")
        parser.add_argument("--session", "--resume", dest="session_id")
        parser.add_argument("--list-sessions", action="store_true")
        parser.add_argument("--delete-session", dest="delete_session")
        parser.add_argument("--provider")
        parser.add_argument("--model")
        return parser

    def run(self, args):
        parser = self._parser()
        try:
            options = parser.parse_args(list(args or []))
        except SystemExit:
            return

        if options.list_sessions:
            for session in self.sessions.list():
                print(f"{session.id}\t{session.updated_at}\t{len(session.messages)} messages")
            return

        if options.delete_session:
            print("Session deleted." if self.sessions.delete(options.delete_session) else "Session not found.")
            return

        session = self.sessions.get(options.session_id) if options.session_id else None
        if options.session_id and session is None:
            print(f"Session not found: {options.session_id}")
            return
        if session is None:
            session = self.sessions.create(provider=options.provider, model=options.model)
        elif options.provider:
            session.provider = options.provider
        if options.model:
            session.model = options.model
        self.sessions.save(session)

        prompt = " ".join(options.prompt).strip()
        if options.interactive or not prompt:
            self._repl(session)
            return
        self._turn(session, prompt)

    def _turn(self, session, prompt: str) -> None:
        request = session.prompt(prompt)
        session.add("user", prompt)
        self.sessions.save(session)
        try:
            response = self.client.chat(request, provider=session.provider)
        except TypeError:
            response = self.client.chat(request)
        except KeyboardInterrupt:
            print("\nInterrupted; session preserved.")
            return
        except Exception as exc:
            print(f"Provider error: {exc}")
            return
        response = str(response)
        print(response)
        session.add("assistant", response)
        self.sessions.save(session)

    def _repl(self, session) -> None:
        print(f"Session: {session.id}")
        print("Commands: /exit, /quit, /sessions, /provider NAME, /model NAME, /clear")
        while True:
            try:
                prompt = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession saved. Goodbye.")
                self.sessions.save(session)
                return
            if not prompt:
                continue
            if prompt in {"/exit", "/quit"}:
                self.sessions.save(session)
                print("Session saved.")
                return
            if prompt == "/sessions":
                for item in self.sessions.list():
                    print(f"{item.id}\t{item.updated_at}\t{len(item.messages)} messages")
                continue
            if prompt.startswith("/provider "):
                session.provider = prompt.split(None, 1)[1].strip() or None
                self.sessions.save(session)
                print(f"Provider: {session.provider or 'default'}")
                continue
            if prompt.startswith("/model "):
                session.model = prompt.split(None, 1)[1].strip() or None
                self.sessions.save(session)
                print(f"Model: {session.model or 'default'}")
                continue
            if prompt == "/clear":
                session.messages.clear()
                self.sessions.save(session)
                print("Conversation context cleared.")
                continue
            self._turn(session, prompt)
