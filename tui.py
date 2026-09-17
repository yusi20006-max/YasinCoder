"""Responsive, dependency-free Terminal UI for YasinCoder.

The UI deliberately uses the standard library so it remains usable on native
Termux installations without pulling a large rendering stack. It reads the
same project, Git, model and command interfaces as the existing CLI.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

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
BLUE = "\x1b[34m"


def _supports_ansi() -> bool:
    if os.getenv("NO_COLOR") or not sys.stdout.isatty():
        return False
    return os.getenv("TERM", "").lower() not in {"dumb", "unknown"}


def _paint(text: str, code: str, enabled: bool) -> str:
    return f"{code}{text}{RESET}" if enabled else text


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


class YasinCoderTUI:
    """Small state-driven terminal dashboard with a plain fallback."""

    def __init__(self) -> None:
        self.ansi = _supports_ansi()
        self.width, self.height = _terminal_size()
        self.project = Path.cwd()
        self.mode = "simple"
        self.running = True

    def refresh_size(self) -> None:
        self.width, self.height = _terminal_size()

    def header(self, title: str) -> None:
        self.refresh_size()
        line = "─" * self.width
        print(_paint(" YASIN CODER ", BOLD + CYAN, self.ansi) + _paint(f"  {title}", BOLD, self.ansi))
        print(_paint(line, DIM, self.ansi))

    def footer(self) -> None:
        print(_paint("─" * self.width, DIM, self.ansi))
        print(_paint("[1] Dashboard  [2] Task  [3] Projects  [4] Sessions  [5] Models  [6] Git  [7] Tests  [8] System  [9] Settings  [q] Quit", DIM, self.ansi))

    def dashboard(self) -> None:
        self.header("Dashboard")
        try:
            info = project_info()
            git = GitManager(self.project).change_summary()
            model = ModelManager().default()
            import importlib.metadata as metadata
            version = metadata.version("yasincoder")
        except Exception as exc:
            print(_paint(f"Unable to read dashboard state: {exc}", RED, self.ansi))
            self.footer(); return
        provider = str(model.get("type", "none")) if model else "none"
        model_name = str(model.get("model") or model.get("name") or "none") if model else "none"
        status = _paint("READY", GREEN, self.ansi)
        if git.get("conflicts"):
            status = _paint("ERROR: git conflicts", RED, self.ansi)
        elif git.get("dirty"):
            status = _paint("READY · changes", YELLOW, self.ansi)
        rows = [
            ("Version", version), ("Project", str(info["project"])),
            ("Branch", git.get("branch") or "not a Git repository"),
            ("Provider", provider), ("Model", model_name),
            ("Status", status), ("Python", sys.version.split()[0]),
            ("Files", info["count"]),
        ]
        for key, value in rows:
            print(f"  {_paint(key + ':', BOLD, self.ansi):<18} {_clip(str(value), self.width - 22)}")
        print()
        print(_paint("What would you like to do?", BOLD, self.ansi))
        print("  1  Start a coding task")
        print("  2  Inspect project and changes")
        print("  3  Choose provider/model")
        print("  4  Run tests")
        print("  5  System status")
        self.footer()

    def task(self) -> None:
        self.header("New Task")
        print("Describe the coding task. Leave empty to cancel.")
        task = input("> ").strip()
        if not task:
            return
        print(_paint("Planning…", CYAN, self.ansi))
        started = time.monotonic()
        try:
            from commands.autonomous import AutonomousCommand
            result = AutonomousCommand().run(task)
            elapsed = time.monotonic() - started
            print(_paint(f"Done · {elapsed:.1f}s", GREEN, self.ansi))
            print(_clip(result, self.width))
        except Exception as exc:
            print(_paint(f"Task failed: {exc}", RED, self.ansi))
        input("Press Enter to continue…")

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
            print(_paint(str(exc), RED, self.ansi))
        self.footer()

    def sessions(self) -> None:
        self.header("Sessions")
        state_root = Path(os.getenv("YASIN_CONFIG_DIR", Path.home() / ".config" / "yasin-coder"))
        candidates = list(state_root.glob("**/*session*")) if state_root.exists() else []
        if candidates:
            for path in candidates[: self.height - 7]:
                print(f"  {path}")
        else:
            print(_paint("No persistent session records are exposed by the current core.", DIM, self.ansi))
            print("The TUI does not invent session state.")
        self.footer()

    def models(self) -> None:
        self.header("Providers & Models")
        manager = ModelManager()
        try:
            models = manager.list()
            default = manager.default()
            if not models:
                print("No configured models. Use: yasincoder setup gemini")
            for item in models:
                active = default and item.get("name") == default.get("name")
                marker = "●" if active else "○"
                state = "active" if active else "configured"
                print(f" {marker} {_clip(str(item.get('name')), self.width - 30)}  {item.get('type', '')}  {state}")
        except Exception as exc:
            print(_paint(f"Model registry error: {exc}", RED, self.ansi))
        self.footer()

    def git(self) -> None:
        self.header("Git / Changes")
        manager = GitManager(self.project)
        if not manager.is_repository():
            print("Current project is not a Git repository.")
            self.footer(); return
        summary = manager.change_summary()
        print(f"Branch: {summary['branch']}")
        print(f"State: {'dirty' if summary['dirty'] else 'clean'}")
        if summary["conflicts"]:
            print(_paint("Conflicts detected. No destructive action is offered by the TUI.", RED, self.ansi))
        print(f"Changed files: {summary['changed']}")
        for entry in summary["entries"][: self.height - 11]:
            print("  " + _clip(entry, self.width - 4))
        print("\nRecent commits:")
        for line in manager.log(5).splitlines():
            print("  " + _clip(line, self.width - 4))
        self.footer()

    def tests(self) -> None:
        self.header("Tests")
        print("Running the repository test suite…")
        started = time.monotonic()
        try:
            proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], text=True, capture_output=True, timeout=300)
            elapsed = time.monotonic() - started
            state = _paint("PASS", GREEN, self.ansi) if proc.returncode == 0 else _paint("FAIL", RED, self.ansi)
            print(f"Result: {state} · {elapsed:.1f}s")
            output = (proc.stdout + proc.stderr).strip().splitlines()
            for line in output[-min(self.height - 8, 12):]:
                print(_clip(line, self.width))
        except subprocess.TimeoutExpired:
            print(_paint("Test run timed out after 300s.", RED, self.ansi))
        self.footer()

    def system(self) -> None:
        self.header("System Status")
        checks: list[tuple[str, str]] = [("Python", sys.version.split()[0]), ("Platform", sys.platform), ("Terminal", f"{self.width}×{self.height}")]
        try:
            import importlib.metadata as metadata
            checks.append(("YasinCoder", metadata.version("yasincoder")))
        except Exception:
            checks.append(("YasinCoder", "source checkout"))
        try:
            git = GitManager(self.project)
            checks.append(("Git", "OK" if git.is_repository() else "not a repository"))
        except Exception as exc:
            checks.append(("Git", f"error: {exc}"))
        try:
            model = ModelManager().default()
            checks.append(("Provider", str(model.get("type")) if model else "none configured"))
        except Exception as exc:
            checks.append(("Provider", f"error: {exc}"))
        for key, value in checks:
            print(f"  {_paint(key + ':', BOLD, self.ansi):<18} {value}")
        self.footer()

    def settings(self) -> None:
        self.header("Settings")
        print(f"UI mode: {self.mode}")
        print("  m  toggle Simple / Advanced")
        print("  r  refresh terminal dimensions")
        print("  n  disable ANSI colors (NO_COLOR for next launch)")
        print("\nSettings are intentionally limited here; provider secrets remain managed by the existing secure setup flow.")
        self.footer()

    def plain(self) -> None:
        """Non-interactive-friendly fallback for dumb or redirected terminals."""
        self.dashboard()
        print("\nRich navigation is unavailable. Use the existing CLI commands directly.")

    def run(self) -> int:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            self.plain()
            return 0
        screens: dict[str, Callable[[], None]] = {"1": self.dashboard, "2": self.task, "3": self.projects, "4": self.sessions, "5": self.models, "6": self.git, "7": self.tests, "8": self.system, "9": self.settings}
        self.dashboard()
        while self.running:
            try:
                choice = input("\nSelect [1-9/q]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if choice == "q":
                break
            if choice == "m":
                self.mode = "advanced" if self.mode == "simple" else "simple"
                self.dashboard()
                continue
            screen = screens.get(choice)
            if screen:
                _clear(self.ansi)
                screen()
            else:
                print("Choose 1-9 or q.")
        if self.ansi:
            print(RESET, end="")
        return 0


def run() -> int:
    return YasinCoderTUI().run()


if __name__ == "__main__":
    raise SystemExit(run())
