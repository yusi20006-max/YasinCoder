"""Safe, explicit Git operations for coding workflows."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    """Base error for safe Git operations."""


class GitDirtyWorktreeError(GitError):
    """Raised when an operation requires a clean worktree."""


@dataclass(frozen=True)
class GitResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    returncode: int = 0


class GitManager:
    """Small, non-destructive Git facade rooted at a project directory."""

    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or Path.cwd()).expanduser().resolve()

    def _run(self, *args: str, check: bool = False) -> GitResult:
        if not args:
            raise ValueError("git arguments are required")
        result = subprocess.run(
            ["git", *args], cwd=self.root, capture_output=True, text=True, check=False
        )
        if check and result.returncode:
            raise GitError(result.stderr.strip() or result.stdout.strip() or "git command failed")
        return GitResult(result.returncode == 0, result.stdout, result.stderr, result.returncode)

    def is_repository(self) -> bool:
        return self._run("rev-parse", "--is-inside-work-tree").stdout.strip() == "true"

    def status(self) -> str:
        return self._run("status", "--short", "--branch").stdout

    def diff(self, staged: bool = False) -> str:
        return self._run("diff", "--cached" if staged else "").stdout if staged else self._run("diff").stdout

    def log(self, limit: int = 20) -> str:
        limit = max(1, min(int(limit), 100))
        return self._run("log", f"-{limit}", "--oneline", "--decorate").stdout

    def branches(self) -> list[str]:
        result = self._run("branch", "--format=%(refname:short)")
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def is_dirty(self) -> bool:
        return bool(self._run("status", "--porcelain").stdout.strip())

    def current_branch(self) -> str:
        return self._run("branch", "--show-current", check=True).stdout.strip()

    def change_summary(self) -> dict[str, object]:
        status = self._run("status", "--porcelain=v1").stdout.splitlines()
        return {
            "branch": self.current_branch() if self.is_repository() else "",
            "dirty": bool(status),
            "changed": len(status),
            "entries": status,
        }

    def stage(self, *paths: str) -> GitResult:
        if not paths:
            raise ValueError("refusing to stage without explicit paths")
        return self._run("add", "--", *paths)

    def commit(self, message: str, *, paths: tuple[str, ...] = ()) -> str:
        message = str(message).strip()
        if not message:
            raise ValueError("commit message is required")
        if paths:
            result = self.stage(*paths)
            if not result.ok:
                raise GitError(result.stderr.strip() or "git add failed")
        result = self._run("diff", "--cached", "--quiet")
        if result.returncode == 0:
            raise GitError("nothing staged to commit")
        self._run("commit", "-m", message, check=True)
        return self._run("rev-parse", "HEAD", check=True).stdout.strip()

    def restore(self, paths: tuple[str, ...] = ()) -> GitResult:
        """Restore tracked working-tree files only; never resets commits or untracked files."""
        args = ["restore"]
        if paths:
            args.extend(["--", *paths])
        else:
            args.extend(["--", "."])
        return self._run(*args)

    def commit_message(self) -> str:
        return "feat: update by YasinCoder"
