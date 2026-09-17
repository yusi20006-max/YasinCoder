"""Secure, optional GitHub integration primitives for YasinCoder."""
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
    """Authentication is unavailable."""
class GitHubPermissionError(GitHubError):
    """A required capability was not explicitly granted."""


@dataclass(frozen=True)
class GitHubCapabilities:
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
    token: str = ""
    api_url: str = "https://api.github.com"
    owner: str = ""
    repo: str = ""
    timeout: float = 20.0
    capabilities: GitHubCapabilities = field(default_factory=GitHubCapabilities)
    @classmethod
    def from_env(cls) -> "GitHubConfig":
        truthy = lambda n: os.getenv(n, "0").lower() in {"1", "true", "yes"}
        try: timeout = max(1.0, float(os.getenv("YASIN_GITHUB_TIMEOUT", "20")))
        except ValueError: timeout = 20.0
        return cls(os.getenv("GITHUB_TOKEN", "").strip(), os.getenv("YASIN_GITHUB_API_URL", "https://api.github.com").rstrip("/"), os.getenv("YASIN_GITHUB_OWNER", "").strip(), os.getenv("YASIN_GITHUB_REPO", "").strip(), timeout, GitHubCapabilities(truthy("YASIN_GITHUB_READ"), truthy("YASIN_GITHUB_ISSUE_WRITE"), truthy("YASIN_GITHUB_BRANCH_WRITE"), truthy("YASIN_GITHUB_PUSH"), truthy("YASIN_GITHUB_PR_WRITE"), truthy("YASIN_GITHUB_MERGE")))
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
    """Small stdlib-only REST client with capability enforcement."""
    _TOKEN_RE = re.compile(r"(?i)(bearer\s+|token\s+)[^\s,;]+")
    def __init__(self, config: GitHubConfig, opener: Callable[..., Any] | None = None) -> None:
        self.config, self._opener, self.audit_log = config, (opener or urllib.request.urlopen), []
    def _require(self, capability: str) -> None:
        if not self.config.capabilities.allows(capability): raise GitHubPermissionError(f"GitHub capability denied: {capability}")
        if not self.config.token: raise GitHubAuthError("GitHub token is not configured")
    def _request(self, method: str, path: str, *, capability: str = "read", payload: Mapping[str, Any] | None = None) -> Any:
        self._require(capability)
        self.audit_log.append(AuditEvent(path.split("?", 1)[0], method, path.split("?", 1)[0], True))
        request = urllib.request.Request(self.config.api_url + "/" + path.lstrip("/"), data=json.dumps(payload).encode() if payload is not None else None, headers={"Accept":"application/vnd.github+json", "X-GitHub-Api-Version":"2022-11-28", "User-Agent":"YasinCoder-GitHubMode/1", "Authorization":f"Bearer {self.config.token}"}, method=method)
        try:
            with self._opener(request, timeout=self.config.timeout) as response: raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            try: detail = exc.read().decode("utf-8", errors="replace")[:500]
            except Exception: detail = ""
            raise GitHubError(self._redact(f"GitHub HTTP {exc.code}: {detail}")) from None
        except urllib.error.URLError as exc: raise GitHubError(self._redact(f"GitHub network error: {exc.reason}")) from None
        if not raw: return None
        try: return json.loads(raw)
        except json.JSONDecodeError: return raw
    def _redact(self, text: str) -> str:
        return self._TOKEN_RE.sub(r"\1[REDACTED]", text.replace(self.config.token, "[REDACTED]") if self.config.token else text)
    def get_repo(self) -> Any:
        if not self.config.repo_full_name: raise GitHubError("GitHub repository identity is not configured")
        return self._request("GET", f"repos/{self.config.repo_full_name}")
    def list_issues(self, state: str = "open", *, page: int = 1, per_page: int = 30) -> Any:
        if state not in {"open", "closed", "all"}: raise ValueError("state must be open, closed, or all")
        if page < 1 or not 1 <= per_page <= 100: raise ValueError("invalid pagination")
        return self._request("GET", f"repos/{self.config.repo_full_name}/issues?state={state}&page={page}&per_page={per_page}")
    def get_issue(self, number: int) -> Any:
        if number < 1: raise ValueError("issue number must be positive")
        return self._request("GET", f"repos/{self.config.repo_full_name}/issues/{number}")
    def create_issue(self, title: str, body: str = "") -> Any:
        if not title.strip(): raise ValueError("issue title must not be empty")
        return self._request("POST", f"repos/{self.config.repo_full_name}/issues", capability="issue_write", payload={"title":title.strip(),"body":body})
    def comment_issue(self, number: int, body: str) -> Any:
        if number < 1 or not body.strip(): raise ValueError("issue number and comment body are required")
        return self._request("POST", f"repos/{self.config.repo_full_name}/issues/{number}/comments", capability="issue_write", payload={"body":body})
    def permissions_snapshot(self) -> dict[str, bool]:
        return {name: self.config.capabilities.allows(name) for name in ("read","issue_write","branch_write","push","pr_write","merge")}
