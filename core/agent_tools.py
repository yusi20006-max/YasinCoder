"""Explicit, observable tools for the YasinCoder coding agent.

All filesystem operations are confined to the configured workspace. Mutating
file operations default to dry-run so callers can present a patch before
applying changes.
"""
from __future__ import annotations

import difflib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

from config import PROJECT_PATH


class ToolError(RuntimeError):
    """A user-facing tool failure with a stable error category."""


def _workspace(root: str | os.PathLike[str] | None = None) -> Path:
    return Path(root or PROJECT_PATH).expanduser().resolve()


def safe_path(path: str, root: str | os.PathLike[str] | None = None) -> Path:
    workspace = _workspace(root)
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = workspace / candidate
    candidate = candidate.resolve()
    try:
        candidate.relative_to(workspace)
    except ValueError as exc:
        raise ToolError("path escapes configured workspace") from exc
    return candidate


def result(ok: bool, tool: str, **data: Any) -> dict[str, Any]:
    return {"ok": ok, "tool": tool, **data}


def workspace_info(root: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    workspace = _workspace(root)
    return result(True, "workspace.info", path=str(workspace), exists=workspace.exists())


def read_file(path: str, root: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    target = safe_path(path, root)
    if not target.is_file():
        return result(False, "file.read", error="file not found", path=str(target))
    return result(True, "file.read", path=str(target), content=target.read_text(encoding="utf-8"))


def write_file(path: str, content: str, *, apply: bool = False,
               root: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    target = safe_path(path, root)
    old = target.read_text(encoding="utf-8") if target.exists() else ""
    patch = "".join(difflib.unified_diff(
        old.splitlines(keepends=True), content.splitlines(keepends=True),
        fromfile=str(target), tofile=str(target),
    ))
    if not apply:
        return result(True, "file.write", applied=False, path=str(target), patch=patch)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return result(True, "file.write", applied=True, path=str(target), patch=patch)


def search(pattern: str, *, root: str | os.PathLike[str] | None = None,
           paths: Iterable[str] | None = None) -> dict[str, Any]:
    workspace = _workspace(root)
    cmd = ["rg", "--line-number", "--no-heading", pattern]
    if paths:
        cmd.extend(str(safe_path(p, workspace)) for p in paths)
    else:
        cmd.append(str(workspace))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        # Portable fallback for environments without ripgrep.
        import re
        regex = re.compile(pattern)
        matches: list[str] = []
        for file in workspace.rglob("*"):
            if not file.is_file() or ".git" in file.parts:
                continue
            try:
                for n, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
                    if regex.search(line):
                        matches.append(f"{file}:{n}:{line}")
            except (UnicodeDecodeError, OSError):
                continue
        return result(True, "search", backend="python", matches=matches)
    return result(proc.returncode in (0, 1), "search", backend="ripgrep", matches=proc.stdout.splitlines(), error=proc.stderr or None)


def shell(command: str, *, root: str | os.PathLike[str] | None = None,
          timeout: int = 60) -> dict[str, Any]:
    workspace = _workspace(root)
    proc = subprocess.run(command, shell=True, cwd=workspace, capture_output=True,
                          text=True, timeout=timeout)
    return result(proc.returncode == 0, "shell.exec", command=command,
                  stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)


def git(args: list[str], *, root: str | os.PathLike[str] | None = None,
        timeout: int = 60) -> dict[str, Any]:
    workspace = _workspace(root)
    proc = subprocess.run(["git", *args], cwd=workspace, capture_output=True,
                          text=True, timeout=timeout)
    return result(proc.returncode == 0, "git.exec", args=args,
                  stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)


def test(command: str = "python -m pytest", *, root: str | os.PathLike[str] | None = None,
         timeout: int = 300) -> dict[str, Any]:
    return shell(command, root=root, timeout=timeout) | {"tool": "test.run"}


def execute(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch one explicit tool call and return JSON-safe structured output."""
    payload = payload or {}
    tools = {
        "workspace.info": workspace_info,
        "file.read": read_file,
        "file.write": write_file,
        "search": search,
        "shell.exec": shell,
        "git.exec": git,
        "test.run": test,
    }
    if name not in tools:
        return result(False, name, error="unknown tool")
    try:
        return tools[name](**payload)
    except (ToolError, OSError, subprocess.SubprocessError, ValueError) as exc:
        return result(False, name, error=str(exc))


def dumps(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
