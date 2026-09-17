"""Secure, optional GitHub integration primitives for YasinCoder.

The module is deliberately independent from the TUI and autonomous planner.
Mutating capabilities are deny-by-default and every request is auditable without
recording credentials or authorization headers.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping


class GitHubError(RuntimeError):
    """Base error for GitHub Mode operations."""


class GitHubAuthError(GitHubError):
    """Raised when authentication is missing or rejected."""


class GitHubPermissionError(GitHubError):
    """Raised when a capability has not been explicitly granted."""


@dataclass(frozen=True)
class GitHubCapabilities:
    """Explicit capabilities; all remote mutations are disabled by default."""

    read: bool = False
    issue_write: bool = False
    branch_write: bool = False
    push: bool = False
    pr_write: bool = False
    merge: bool = False

    def allows(self, capability: str) -> bool:
        return bool(getattr(self, capability, False))


@dataclass(frozen=True)
class GitHubConfig:
    """Configuration sourced from environment; no credential persistence."""

    token: str = ""
    api_url: str = "https://api.github.com"
    owner: str = ""
    repo: str = ""
    timeout: float = 20.0
    capabilities: GitHubCapabilities = field(default_factory=GitHubCapabilities)

    @classmethod
    def from_env(cls) -> "GitHubConfig":
        token = os.getenv("GITHUB_TOKEN", "").strip()
        owner = os.getenv("YASIN_GITHUB_OWNER", "").strip()
        repo = os.getenv("YASIN_GITHUB_REPO", "").strip()
        try:
            timeout = max(1.0, float(os.getenv("YASIN_GITHUB_TIMEOUT", "20")))
        except ValueError:
            timeout = 20.0
        caps = GitHubCapabilities(
            read=os.getenv("YASIN_GITHUB_READ", "0").lower() in {"1", "true", "yes"},
            issue_write=os.getenv("YASIN_GITHUB_ISSUE_WRITE", "0").lower() in {"1", "true", "yes"},
            branch_write=os.getenv("YASIN_GITHUB_BRANCH_WRITE", "0").lower() in {"1", "true", "yes"},
            push=os.getenv("YASIN_GITHUB_PUSH", "0").lower() in {"1", "true", "yes"},
            pr_write=os.getenv("YASIN_GITHUB_PR_WRITE", "0").lower() in {"1", "true", "yes"},
            merge=os.getenv("YASIN_GITHUB_MERGE", "0").lower() in {"1", "true", "yes"},
        )
        return cls(token=token, api_url=os.getenv("YASIN_GITHUB_API_URL", "https://api.github.com").rstrip("/"), owner=owner, repo=repo, timeout=timeout, capabilities=caps)

    @property
    def repo_full_name(self) -> str:
        return f"{self.owner}/{self.repo}" if self.owner and self.repo else ""


@dataclass(frozen=True)
class AuditEvent:
    operation: str
    method: str
    path: str
    allowed: bool


class GitHubClient:
    """Small stdlib-only GitHub REST client with capability enforcement."""

    _TOKEN_RE = re.compile(r"(?i)(bearer\s+|token\s+)[^\s,;]+")

    def __init__(self, config: GitHubConfig, opener: Callable[..., Any] | None = None) -> None:
        self.config = config
        self._opener = opener or urllib.request.urlopen
        self.audit_log: list[AuditEvent] = []

    def _require(self, capability: str) -> None:
        allowed = self.config.capabilities.allows(capability)
        if not allowed:
            raise GitHubPermissionError(f"GitHub capability denied: {capability}")
        if not self.config.token:
            raise GitHubAuthError("GitHub token is not configured")

    def _request(self, method: str, path: str, *, capability: str = "read", payload: Mapping[str, Any] | None = None) -> Any:
        self._require(capability)
        safe_path = path.split("?", 1)[0]
        self.audit_log.append(AuditEvent(method, method, safe_path, True))
        url = self.config.api_url + "/" + path.lstrip("/")
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "YasinCoder-GitHubMode/1",
            "Authorization": f"Bearer {self.config.token}",
        }
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self.config.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception:
                pass
            raise GitHubError(self._redact(f"GitHub HTTP {exc.code}: {detail}")) from None
        except urllib.error.URLError as exc:
            raise GitHubError(self._redact(f"GitHub network error: {exc.reason}")) from None
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def _redact(self, text: str) -> str:
        if self.config.token:
            text = text.replace(self.config.token, "[REDACTED]")
        return self._TOKEN_RE.sub(r"\1[REDACTED]", text)

    def get_repo(self) -> Any:
        if not self.config.repo_full_name:
            raise GitHubError("GitHub repository identity is not configured")
        return self._request("GET", f"repos/{self.config.repo_full_name}")

    def get_issue(self, number: int) -> Any:
        if number < 1:
            raise ValueError("issue number must be positive")
        return self._request("GET", f"repos/{self.config.repo_full_name}/issues/{number}")

    def create_issue(self, title: str, body: str = "") -> Any:
        return self._request("POST", f"repos/{self.config.repo_full_name}/issues", capability="issue_write", payload={"title": title, "body": body})

    def permissions_snapshot(self) -> dict[str, bool]:
        return {name: self.config.capabilities.allows(name) for name in ("read", "issue_write", "branch_write", "push", "pr_write", "merge")}
