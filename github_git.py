"""Controlled local Git commit/push operations for GitHub Mode."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from urllib.parse import urlparse

from github_mode import GitHubClient, GitHubPermissionError


class GitSafetyError(RuntimeError):
    """Raised when a Git safety precondition fails."""


@dataclass
class GitPublisher:
    path: str
    client: GitHubClient

    def _run(self, *args: str) -> str:
        proc = subprocess.run(("git", "-C", self.path, *args), text=True, capture_output=True)
        if proc.returncode:
            raise GitSafetyError(proc.stderr.strip() or "git command failed")
        return proc.stdout.strip()

    def _verify_remote(self, remote: str = "origin") -> None:
        configured = self._run("remote", "get-url", remote)
        parsed = urlparse(configured.replace("git@github.com:", "https://github.com/", 1))
        actual = parsed.path.strip("/").removesuffix(".git")
        expected = self.client.config.repo_full_name.strip("/")
        if expected and actual.lower() != expected.lower():
            raise GitSafetyError(f"remote repository mismatch: expected {expected}")

    def preflight(self, remote: str = "origin") -> dict[str, str]:
        self._verify_remote(remote)
        return {"branch": self._run("branch", "--show-current"), "status": self._run("status", "--short"), "diff": self._run("diff", "--stat")}

    def commit(self, message: str, *, paths: list[str] | None = None) -> str:
        if not self.client.config.capabilities.allows("push"):
            raise GitHubPermissionError("GitHub capability denied: push")
        if not message.strip() or "\n" in message:
            raise ValueError("commit message must be a single non-empty line")
        if paths:
            for path in paths:
                if not path or path.startswith("-") or ".." in path.split("/"):
                    raise GitSafetyError("unsafe commit path")
            self._run("add", "--", *paths)
        else:
            self._run("add", "-A")
        self._run("diff", "--cached", "--quiet")
        self._run("commit", "-m", message.strip())
        return self._run("rev-parse", "HEAD")

    def push(self, remote: str = "origin", branch: str | None = None) -> str:
        if not self.client.config.capabilities.allows("push"):
            raise GitHubPermissionError("GitHub capability denied: push")
        self._verify_remote(remote)
        target = branch or self._run("branch", "--show-current")
        if not target or target.startswith("-") or not re.fullmatch(r"[A-Za-z0-9._/-]+", target):
            raise GitSafetyError("unsafe push branch")
        return self._run("push", remote, target)
