"""Safe local workspace helpers for GitHub Mode."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass

from github_mode import GitHubClient, GitHubPermissionError


_BRANCH_RE = re.compile(r"[^A-Za-z0-9._-]+")


def issue_branch_name(number: int, title: str) -> str:
    """Create a deterministic, safe branch name from an Issue."""
    if number < 1:
        raise ValueError("issue number must be positive")
    slug = _BRANCH_RE.sub("-", title.strip().lower()).strip("-/. ")
    slug = re.sub(r"-+", "-", slug)[:70].strip("-") or "issue"
    return f"issue/{number}-{slug}"


@dataclass
class GitWorkspace:
    path: str

    def _run(self, *args: str) -> str:
        proc = subprocess.run(("git", "-C", self.path, *args), text=True, capture_output=True)
        if proc.returncode:
            raise RuntimeError(proc.stderr.strip() or "git command failed")
        return proc.stdout.strip()

    def status(self) -> str:
        return self._run("status", "--short", "--branch")

    def current_branch(self) -> str:
        return self._run("branch", "--show-current")

    def checkout_existing(self, branch: str) -> str:
        if not branch or branch.startswith("-") or ".." in branch:
            raise ValueError("unsafe branch name")
        return self._run("switch", branch)

    def checkout_new(self, branch: str, *, force: bool = False) -> str:
        if not branch or branch.startswith("-") or ".." in branch:
            raise ValueError("unsafe branch name")
        if force:
            raise GitHubPermissionError("destructive branch replacement is disabled")
        return self._run("switch", "-c", branch)

    def sync_ff_only(self, remote: str = "origin") -> str:
        if remote.startswith("-"):
            raise ValueError("unsafe remote")
        self._run("fetch", remote)
        return self._run("merge", "--ff-only", "FETCH_HEAD")


class GitHubWorkspace:
    """Coordinates Issue-derived branch naming with a local workspace."""
    def __init__(self, client: GitHubClient, workspace: GitWorkspace) -> None:
        self.client, self.workspace = client, workspace

    def branch_for_issue(self, number: int) -> str:
        issue = self.client.get_issue(number)
        return issue_branch_name(number, str(issue.get("title", "issue")))

    def prepare_issue_branch(self, number: int) -> str:
        branch = self.branch_for_issue(number)
        if self.workspace.current_branch() == branch:
            return branch
        self.workspace.checkout_new(branch)
        return branch
