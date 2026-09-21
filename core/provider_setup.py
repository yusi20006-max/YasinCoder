"""Provider-agnostic interactive setup gateway."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Callable, Sequence

from core.gemini_setup import GeminiSetupError, interactive_setup as interactive_gemini_setup


@dataclass(frozen=True)
class ProviderOption:
    key: str
    label: str
    available: bool


PROVIDERS: tuple[ProviderOption, ...] = (
    ProviderOption("gemini", "Gemini", True),
    ProviderOption("openai", "OpenAI / compatible", False),
    ProviderOption("cloudflare", "Cloudflare", False),
)


def _read_key() -> str:
    """Read one navigation key without requiring a third-party UI library."""
    if os.name == "nt":
        import msvcrt

        first = msvcrt.getwch()
        if first in ("\\x00", "\\xe0"):
            second = msvcrt.getwch()
            return {"H": "up", "P": "down"}.get(second, "")
        if first in ("\\r", "\\n"):
            return "enter"
        if first == "\\x1b":
            return "esc"
        return first

    import termios
    import tty

    fd = sys.stdin.fileno()
    previous = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first == "\\x1b":
            second = sys.stdin.read(1)
            if second == "[":
                third = sys.stdin.read(1)
                return {"A": "up", "B": "down"}.get(third, "esc")
            return "esc"
        if first in ("\\r", "\\n"):
            return "enter"
        if first == "\\x03":
            raise KeyboardInterrupt
        return first
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, previous)


def _interactive_available() -> bool:
    return bool(sys.stdin.isatty() and sys.stdout.isatty())


def _render(options: Sequence[ProviderOption], selected: int, output: Callable[[str], None]) -> None:
    if _interactive_available():
        output("\\x1b[2J\\x1b[H")
    output("YasinCoder AI setup")
    output("Select a provider with ↑/↓ and Enter. Esc cancels.")
    output("")
    for index, option in enumerate(options):
        marker = "❯" if index == selected else " "
        state = "" if option.available else " (not implemented)"
        output(f"{marker} {option.label}{state}")


def select_provider(
    options: Sequence[ProviderOption] = PROVIDERS,
    *,
    key_reader: Callable[[], str] | None = None,
    output: Callable[[str], None] = print,
) -> str | None:
    """Return the selected provider key, or None when cancelled/unavailable."""
    if not options:
        return None
    reader = key_reader or _read_key
    selected = 0
    while True:
        _render(options, selected, output)
        key = reader()
        if key == "up":
            selected = (selected - 1) % len(options)
        elif key == "down":
            selected = (selected + 1) % len(options)
        elif key == "enter":
            option = options[selected]
            if not option.available:
                output(f"{option.label} is not implemented yet.")
                continue
            return option.key
        elif key in ("esc", "q", "\\x03"):
            return None


def interactive_setup(manager=None):
    """Run the provider gateway and dispatch to the selected provider setup."""
    if not _interactive_available():
        output = print
        output("Interactive provider selection requires a terminal.")
        output("Use: yasincoder setup gemini")
        return interactive_gemini_setup(manager=manager)

    selected = select_provider()
    if selected is None:
        print("Setup cancelled.")
        return None
    if selected == "gemini":
        try:
            return interactive_gemini_setup(manager=manager)
        except GeminiSetupError:
            raise
    raise SystemExit(f"Provider '{selected}' is not implemented")
