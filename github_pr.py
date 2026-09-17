"""Pull Request operations built on the secure GitHub Mode client."""
from __future__ import annotations

from dataclasses import dataclass

from github_mode import GitHubClient, GitHubPermissionError


@dataclass(frozen=True)
class PullRequestRef:
    number: int
    url: str
    state: str
    head: str
    base: str


class GitHubPullRequests:
    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    def create(self, title: str, head: str, base: str = "master", body: str = "") -> dict:
        if not title.strip() or not head.strip() or not base.strip():
            raise ValueError("title, head and base are required")
        return self.client._request("POST", f"repos/{self.client.config.repo_full_name}/pulls", capability="pr_write", payload={"title":title.strip(),"head":head.strip(),"base":base.strip(),"body":body})

    def get(self, number: int) -> dict:
        if number < 1: raise ValueError("PR number must be positive")
        return self.client._request("GET", f"repos/{self.client.config.repo_full_name}/pulls/{number}")

    def list_open(self, *, page: int = 1, per_page: int = 30) -> list:
        if page < 1 or not 1 <= per_page <= 100: raise ValueError("invalid pagination")
        return self.client._request("GET", f"repos/{self.client.config.repo_full_name}/pulls?state=open&page={page}&per_page={per_page}")

    def comment(self, number: int, body: str) -> dict:
        if not body.strip(): raise ValueError("comment body is required")
        return self.client._request("POST", f"repos/{self.client.config.repo_full_name}/issues/{number}/comments", capability="pr_write", payload={"body":body})

    @staticmethod
    def summary(pr: dict) -> PullRequestRef:
        return PullRequestRef(int(pr["number"]), str(pr.get("html_url", "")), str(pr.get("state", "")), str(pr.get("head", {}).get("ref", "")), str(pr.get("base", {}).get("ref", "")))
