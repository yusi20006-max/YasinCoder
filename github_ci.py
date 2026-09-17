"""Read-only GitHub Actions CI diagnostics."""
from __future__ import annotations

from dataclasses import dataclass

from github_mode import GitHubClient


@dataclass(frozen=True)
class CIRun:
    id: int
    name: str
    status: str
    conclusion: str | None
    url: str
    sha: str


class GitHubActions:
    """Discovers workflow runs and provides compact PR/commit diagnostics."""
    def __init__(self, client: GitHubClient) -> None:
        self.client = client

    def runs_for_commit(self, sha: str, *, page: int = 1, per_page: int = 30) -> list[CIRun]:
        if not sha or any(ch not in "0123456789abcdefABCDEF" for ch in sha) or not 7 <= len(sha) <= 64:
            raise ValueError("invalid commit SHA")
        if page < 1 or not 1 <= per_page <= 100: raise ValueError("invalid pagination")
        data = self.client._request("GET", f"repos/{self.client.config.repo_full_name}/actions/runs?head_sha={sha}&page={page}&per_page={per_page}")
        return [CIRun(int(r["id"]), str(r.get("name", "")), str(r.get("status", "")), r.get("conclusion"), str(r.get("html_url", "")), str(r.get("head_sha", sha))) for r in data.get("workflow_runs", [])]

    @staticmethod
    def failed(runs: list[CIRun]) -> list[CIRun]:
        return [run for run in runs if run.conclusion == "failure"]

    @staticmethod
    def all_successful(runs: list[CIRun]) -> bool:
        return bool(runs) and all(run.conclusion == "success" for run in runs)
