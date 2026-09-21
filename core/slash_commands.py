"""User-friendly slash command definitions and completion for the TUI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SlashCommand:
    name: str
    description: str
    action: str


SLASH_COMMANDS: tuple[SlashCommand, ...] = (
    SlashCommand("/help", "Show available slash commands", "help"),
    SlashCommand("/model", "Show configured provider/model", "models"),
    SlashCommand("/provider", "Show configured providers/models", "models"),
    SlashCommand("/test", "Run the repository tests", "tests"),
    SlashCommand("/review", "Review a file (use /review <file>)", "review"),
    SlashCommand("/fix", "Fix a file (use /fix <file>)", "fix"),
    SlashCommand("/plan", "Create and review a plan (use /plan <task>)", "plan"),
    SlashCommand("/act", "Execute a coding task (use /act <task>)", "act"),
    SlashCommand("/clear", "Clear the current prompt", "clear"),
    SlashCommand("/quit", "Exit YasinCoder", "quit"),
)


def complete(prefix: str) -> list[SlashCommand]:
    """Return commands matching the typed prefix, ordered predictably."""
    if not prefix.startswith("/"):
        return []
    value = prefix.lower()
    return [command for command in SLASH_COMMANDS if command.name.startswith(value)]


def parse(text: str) -> tuple[SlashCommand | None, str]:
    """Resolve a slash command and return its remaining argument."""
    stripped = text.strip()
    if not stripped.startswith("/"):
        return None, stripped
    head, _, argument = stripped.partition(" ")
    for command in SLASH_COMMANDS:
        if command.name == head.lower():
            return command, argument.strip()
    return None, stripped
