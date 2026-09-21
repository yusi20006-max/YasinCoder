"""Responsive, dependency-free prompt-first Terminal UI for YasinCoder.

The UI deliberately uses the standard library so it remains usable on native
Termux installations without pulling a large rendering stack.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from core.diagnostics import from_exception
from core.file_mentions import complete as complete_mentions, context_preview, enrich_prompt, mentions
from core.slash_commands import SLASH_COMMANDS, complete as complete_slash, parse as parse_slash
from git_manager import GitManager
from models.manager import ModelManager
from project import project_info


RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"
CYAN = "\x1b[36m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
RED = "\x1b[31m"


def _supports_ansi() -> bool:
    if os.getenv("NO_COLOR") or not sys.stdout.isatty():
        return False
    return os.getenv("TERM", "").lower() not in {"dumb", "unknown"}


def _paint(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{RESET}" if enabled else text


def _supports_unicode() -> bool:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    return encoding.lower().replace("-", "") in {"utf8", "utf16", "utf32"}


def _line(width: int) -> str:
    return ("─" if _supports_unicode() else "-") * width


def _clip(text: str, width: int) -> str:
    text = str(text).replace("\t", " ").replace("\r", "")
    if width <= 1:
        return text[:width]
    return text if len(text) <= width else text[: width - 1] + "…"


def _terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size((80, 24))
    return max(40, size.columns), max(12, size.lines)


def _clear(enabled: bool) -> None:
    if enabled:
        print("\x1b[2J\x1b[H", end="")
    else:
        print("\n" * 2, end="")


def _read_key() -> str:
    """Read one key and restore terminal mode even when an error occurs."""
    if os.name == "nt":
        import msvcrt

        first = msvcrt.getwch()
        if first in ("\x00", "\xe0"):
            second = msvcrt.getwch()
            return {
                "H": "up",
                "P": "down",
                "K": "left",
                "M": "right",
            }.get(second, "")
        if first == "\r":
            return "enter"
        if first == "\x1b":
            return "esc"
        if first == "\x08":
            return "backspace"
        if first == "\x03":
            return "ctrl_c"
        if first == "\x04":
            return "ctrl_d"
        if first == "\x10":
            return "ctrl_p"
        if first == "\t":
            return "tab"
        return first

    import termios
    import tty

    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first == "\x1b":
            second = sys.stdin.read(1)
            if second == "[":
                third = sys.stdin.read(1)
                return {
                    "A": "up",
                    "B": "down",
                    "C": "right",
                    "D": "left",
                }.get(third, "esc")
            return "esc"
        if first in ("\r", "\n"):
            return "enter"
        if first in ("\x7f", "\x08"):
            return "backspace"
        if first == "\x03":
            return "ctrl_c"
        if first == "\x04":
            return "ctrl_d"
        if first == "\x10":
            return "ctrl_p"
        if first == "\t":
            return "tab"
        return first
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


@dataclass(frozen=True)
class PromptAction:
    key: str
    label: str


PROMPT_ACTIONS: tuple[PromptAction, ...] = (
    PromptAction("task", "Start a coding task"),
    PromptAction("project", "Inspect project"),
    PromptAction("models", "Choose provider/model"),
    PromptAction("git", "Inspect Git changes"),
    PromptAction("tests", "Run tests"),
    PromptAction("system", "System status"),
    PromptAction("sessions", "Sessions"),
    PromptAction("settings", "Settings"),
)


class PromptSession:
    """Testable prompt editor with keyboard navigation and command palette."""

    def __init__(
        self,
        key_reader: Callable[[], str],
        output: Callable[[str], None],
        actions: Sequence[PromptAction] = PROMPT_ACTIONS,
        completion_root: Path | None = None,
    ) -> None:
        self.key_reader = key_reader
        self.output = output
        self.actions = tuple(actions)
        self.completion_root = completion_root

    def _render(self, text: str, cursor: int, selected: int | None) -> None:
        self.output("")
        self.output(("❯" if _supports_unicode() else ">") + " " + text)
        slash_matches = complete_slash(text.strip()) if text.strip().startswith("/") else []
        mention_matches = complete_mentions(text.rsplit(" ", 1)[-1], self.completion_root) if self.completion_root and text.rsplit(" ", 1)[-1].startswith("@") else []
        if slash_matches:
            self.output("")
            self.output("Commands:")
            for command in slash_matches[:5]:
                self.output(f"  {command.name:<10} {command.description}")
        if mention_matches:
            self.output("")
            self.output("Files:")
            for item in mention_matches[:5]:
                self.output("  " + item)
        if selected is not None and self.actions:
            self.output("")
            self.output("Quick actions:")
            for index, action in enumerate(self.actions[:5]):
                marker = ("❯" if _supports_unicode() else ">") if index == selected else " "
                self.output(f" {marker} {action.label}")
        self.output("")
        self.output(("↑↓" if _supports_unicode() else "Up/Down") + " Actions/history   Enter Send   Esc Cancel   Ctrl+P Commands   Ctrl+C Exit")

    def run(self) -> tuple[str, str | None]:
        chars: list[str] = []
        cursor = 0
        selected: int | None = 0 if self.actions else None
        history: list[str] = []
        history_index: int | None = None

        while True:
            text = "".join(chars)
            self._render(text, cursor, selected)
            key = self.key_reader()

            if key == "enter":
                if text.strip():
                    history.append(text)
                    return "task", text.strip()
                if selected is not None and self.actions:
                    return "action", self.actions[selected].key
                continue
            if key == "esc":
                return "cancel", None
            if key in {"ctrl_c", "ctrl_d"}:
                return "quit", None
            if key == "ctrl_p":
                return "palette", None
            if key == "up":
                if text or history:
                    if history:
                        if history_index is None:
                            history_index = len(history) - 1
                        else:
                            history_index = max(0, history_index - 1)
                        chars = list(history[history_index])
                        cursor = len(chars)
                        selected = None
                elif self.actions:
                    selected = (selected - 1) % len(self.actions) if selected is not None else 0
                continue
            if key == "down":
                if text or history:
                    if history:
                        if history_index is None:
                            history_index = 0
                        elif history_index < len(history) - 1:
                            history_index += 1
                        else:
                            history_index = None
                            chars = []
                            cursor = 0
                            selected = 0 if self.actions else None
                            continue
                        chars = list(history[history_index])
                        cursor = len(chars)
                        selected = None
                elif self.actions:
                    selected = (selected + 1) % len(self.actions) if selected is not None else 0
                continue
            if key == "left":
                cursor = max(0, cursor - 1)
                selected = None
                continue
            if key == "right":
                cursor = min(len(chars), cursor + 1)
                selected = None
                continue
            if key == "tab":
                token = text.rsplit(" ", 1)[-1]
                if token.startswith("/"):
                    matches = complete_slash(token)
                    if matches:
                        replacement = matches[0].name
                        chars = list(text[: len(text) - len(token)] + replacement)
                        cursor = len(chars)
                        selected = None
                    continue
                if token.startswith("@") and self.completion_root:
                    matches = complete_mentions(token, self.completion_root)
                    if matches:
                        replacement = matches[0]
                        chars = list(text[: len(text) - len(token)] + replacement)
                        cursor = len(chars)
                        selected = None
                continue
            if key == "backspace":
                if cursor > 0:
                    del chars[cursor - 1]
                    cursor -= 1
                selected = None
                continue
            if isinstance(key, str) and len(key) == 1 and key.isprintable():
                chars.insert(cursor, key)
                cursor += 1
                selected = None
                history_index = None


class YasinCoderTUI:
    """Prompt-first terminal UI with a plain/non-TTY fallback."""

    def __init__(self, key_reader: Callable[[], str] | None = None) -> None:
        self.ansi = _supports_ansi()
        self.width, self.height = _terminal_size()
        self.project = Path.cwd()
        self.mode = "simple"
        self.running = True
        self.key_reader = key_reader or _read_key

    def refresh_size(self) -> None:
        self.width, self.height = _terminal_size()

    def header(self, title: str) -> None:
        self.refresh_size()
        print(_paint(" YASIN CODER ", BOLD + CYAN, self.ansi) + _paint(f"  {title}", BOLD, self.ansi))
        print(_paint(_line(self.width), DIM, self.ansi))

    def footer(self) -> None:
        print(_paint(_line(self.width), DIM, self.ansi))
        print(_paint((("↑↓" if _supports_unicode() else "Up/Down") + " Navigate  Enter Select  Esc Back  Ctrl+P Commands  Ctrl+C Exit"), DIM, self.ansi))

    def dashboard(self) -> None:
        self.header("Dashboard")
        try:
            info = project_info()
            git = GitManager(self.project).change_summary()
            model = ModelManager().default()
            import importlib.metadata as metadata
            version = metadata.version("yasincoder")
        except Exception as exc:
            print(_paint(from_exception(exc).message, RED, self.ansi))
            self.footer()
            return
        provider = str(model.get("type", "none")) if model else "none"
        model_name = str(model.get("model") or model.get("name") or "none") if model else "none"
        status = _paint("READY", GREEN, self.ansi)
        if git.get("conflicts"):
            status = _paint("ERROR: git conflicts", RED, self.ansi)
        elif git.get("dirty"):
            status = _paint("READY · changes", YELLOW, self.ansi)
        rows = [
            ("Version", version),
            ("Project", str(info["project"])),
            ("Branch", git.get("branch") or "not a Git repository"),
            ("Provider", provider),
            ("Model", model_name),
            ("Status", status),
            ("Python", sys.version.split()[0]),
            ("Files", info["count"]),
        ]
        for key, value in rows:
            print(f"  {_paint(key + ':', BOLD, self.ansi):<18} {_clip(str(value), self.width - 22)}")
        self.footer()

    def task(self, prompt: str | None = None) -> None:
        self.header("New Task")
        task = prompt
        if task is None:
            result, value = PromptSession(self.key_reader, print, completion_root=self.project).run()
            if result != "task" or not value:
                return
            task = value
        referenced = mentions(task, self.project)
        if referenced:
            print(_paint("Context preview:", CYAN, self.ansi))
            for item in context_preview(referenced, self.project):
                print("  " + item)
            print()
        enriched_task, _ = enrich_prompt(task, self.project)
        print(_paint("Planning...", CYAN, self.ansi))
        started = time.monotonic()
        try:
            from commands.autonomous import AutonomousCommand
            result = AutonomousCommand().run(enriched_task)
            elapsed = time.monotonic() - started
            print(_paint(f"Done · {elapsed:.1f}s", GREEN, self.ansi))
            print(_clip(result, self.width))
        except Exception as exc:
            print(_paint(f"Task failed: {from_exception(exc).message}", RED, self.ansi))
        self._pause()

    def projects(self) -> None:
        self.header("Projects")
        try:
            info = project_info()
            print(f"Path: {info['project']}")
            print(f"Python files: {info['count']}")
            print("\nRecent files:")
            for path in info["files"][: max(3, self.height - 10)]:
                print("  " + _clip(str(path), self.width - 4))
        except Exception as exc:
            print(_paint(from_exception(exc).message, RED, self.ansi))
        self._pause()

    def sessions(self) -> None:
        self.header("Sessions")
        state_root = Path(os.getenv("YASIN_CONFIG_DIR", Path.home() / ".config" / "yasin-coder"))
        candidates = list(state_root.glob("**/*session*")) if state_root.exists() else []
        if candidates:
            for path in candidates[: max(1, self.height - 7)]:
                print(f"  {path}")
        else:
            print(_paint("No persistent session records are exposed by the current core.", DIM, self.ansi))
            print("The TUI does not invent session state.")
        self._pause()

    def models(self) -> None:
        self.header("Providers & Models")
        manager = ModelManager()
        try:
            models = manager.list()
            default = manager.default()
            if not models:
                print("No configured models. Use: yasincoder setup")
            for item in models:
                active = bool(default and item.get("name") == default.get("name"))
                marker = "●" if active and _supports_unicode() else ("*" if active else "-")
                state = "active" if active else "configured"
                print(f" {marker} {_clip(str(item.get('name')), self.width - 30)}  {item.get('type', '')}  {state}")
        except Exception as exc:
            print(_paint(f"Model registry error: {from_exception(exc).message}", RED, self.ansi))
        self._pause()

    def git(self) -> None:
        self.header("Git / Changes")
        manager = GitManager(self.project)
        if not manager.is_repository():
            print("Current project is not a Git repository.")
            self._pause()
            return
        summary = manager.change_summary()
        print(f"Branch: {summary['branch']}")
        print(f"State: {'dirty' if summary['dirty'] else 'clean'}")
        if summary["conflicts"]:
            print(_paint("Conflicts detected. No destructive action is offered by the TUI.", RED, self.ansi))
        print(f"Changed files: {summary['changed']}")
        for entry in summary["entries"][: max(1, self.height - 11)]:
            print("  " + _clip(entry, self.width - 4))
        print("\nRecent commits:")
        for line in manager.log(5).splitlines():
            print("  " + _clip(line, self.width - 4))
        self._pause()

    def tests(self) -> None:
        self.header("Tests")
        print("Running the repository test suite…")
        started = time.monotonic()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
                text=True,
                capture_output=True,
                timeout=300,
            )
            elapsed = time.monotonic() - started
            state = _paint("PASS", GREEN, self.ansi) if proc.returncode == 0 else _paint("FAIL", RED, self.ansi)
            print(f"Result: {state} · {elapsed:.1f}s")
            output = (proc.stdout + proc.stderr).strip().splitlines()
            for line in output[-min(max(1, self.height - 8), 12):]:
                print(_clip(line, self.width))
        except subprocess.TimeoutExpired:
            print(_paint("Test run timed out after 300s.", RED, self.ansi))
        self._pause()

    def system(self) -> None:
        self.header("System Status")
        checks: list[tuple[str, str]] = [
            ("Python", sys.version.split()[0]),
            ("Platform", sys.platform),
            ("Terminal", f"{self.width}×{self.height}"),
        ]
        try:
            import importlib.metadata as metadata
            checks.append(("YasinCoder", metadata.version("yasincoder")))
        except Exception:
            checks.append(("YasinCoder", "source checkout"))
        try:
            git = GitManager(self.project)
            checks.append(("Git", "OK" if git.is_repository() else "not a repository"))
        except Exception as exc:
            checks.append(("Git", f"error: {from_exception(exc).message}"))
        try:
            model = ModelManager().default()
            checks.append(("Provider", str(model.get("type")) if model else "none configured"))
        except Exception as exc:
            checks.append(("Provider", f"error: {from_exception(exc).message}"))
        for key, value in checks:
            print(f"  {_paint(key + ':', BOLD, self.ansi):<18} {value}")
        self._pause()

    def settings(self) -> None:
        self.header("Settings")
        print(f"UI mode: {self.mode}")
        print("Provider secrets remain managed by the secure setup flow.")
        print("The prompt-first workflow uses only standard-library terminal input.")
        self._pause()

    def slash_help(self) -> None:
        self.header("Slash Commands")
        for command in SLASH_COMMANDS:
            print(f"  {command.name:<10} {command.description}")
        print("\nTab completes a command; Enter submits it.")
        self._pause()

    def slash_task(self, command_name: str, argument: str) -> None:
        if command_name == "help":
            self.slash_help()
        elif command_name == "clear":
            return
        elif command_name == "quit":
            self.running = False
        elif command_name == "models":
            self.models()
        elif command_name == "tests":
            self.tests()
        elif command_name == "review":
            if argument:
                self.task(f"Review {argument}")
            else:
                self.header("Review"); print("Usage: /review <file>"); self._pause()
        elif command_name == "fix":
            if argument:
                self.task(f"Fix {argument}")
            else:
                self.header("Fix"); print("Usage: /fix <file>"); self._pause()
        elif command_name == "plan":
            if argument:
                self.task(f"Plan {argument}")
            else:
                self.header("Plan"); print("Usage: /plan <task>"); self._pause()

    def command_palette(self) -> str | None:
        selected = 0
        actions = PROMPT_ACTIONS + (PromptAction("dashboard", "Dashboard"), PromptAction("quit", "Quit"))
        while True:
            _clear(self.ansi)
            self.header("Commands")
            for index, action in enumerate(actions):
                marker = ("❯" if _supports_unicode() else ">") if index == selected else " "
                print(f" {marker} {action.label}")
            self.footer()
            key = self.key_reader()
            if key == "up":
                selected = (selected - 1) % len(actions)
            elif key == "down":
                selected = (selected + 1) % len(actions)
            elif key == "enter":
                return actions[selected].key
            elif key in {"esc", "ctrl_c", "ctrl_d"}:
                return None

    def _pause(self) -> None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            self.key_reader()

    def prompt(self) -> tuple[str, str | None]:
        self.refresh_size()
        self.header("Command")
        try:
            model = ModelManager().default()
            model_name = str(model.get("model") or model.get("name") or "none") if model else "none"
            provider = str(model.get("type") or "none") if model else "none"
        except Exception:
            provider, model_name = "unknown", "unknown"
        print(f"Project: {_clip(str(self.project), self.width - 9)}")
        print(f"Provider: {provider}   Model: {_clip(model_name, max(10, self.width - 25))}")
        print(_line(self.width))
        return PromptSession(self.key_reader, print, completion_root=self.project).run()

    def plain(self) -> None:
        """Non-interactive-friendly fallback for redirected or dumb terminals."""
        self.dashboard()
        print("\nRich keyboard navigation is unavailable. Use the CLI commands directly.")
        print("For the interactive workflow, run: yasincoder tui")

    def run(self) -> int:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            self.plain()
            return 0
        try:
            while self.running:
                _clear(self.ansi)
                action, value = self.prompt()
                if action == "quit":
                    break
                if action == "cancel":
                    continue
                if action == "task" and value:
                    command, argument = parse_slash(value)
                    if command is not None:
                        self.slash_task(command.action, argument)
                    else:
                        self.task(value)
                elif action == "palette":
                    command = self.command_palette()
                    if command:
                        self._dispatch(command)
                elif action == "action" and value:
                    self._dispatch(value)
        except (EOFError, KeyboardInterrupt):
            print()
        finally:
            if self.ansi:
                print(RESET, end="")
        return 0

    def _dispatch(self, action: str) -> None:
        if action == "quit":
            self.running = False
        elif action == "task":
            self.task()
        elif action == "project":
            self.projects()
        elif action == "sessions":
            self.sessions()
        elif action == "models":
            self.models()
        elif action == "git":
            self.git()
        elif action == "tests":
            self.tests()
        elif action == "system":
            self.system()
        elif action == "settings":
            self.settings()
        elif action == "dashboard":
            _clear(self.ansi)
            self.dashboard()


def run() -> int:
    return YasinCoderTUI().run()


if __name__ == "__main__":
    raise SystemExit(run())
