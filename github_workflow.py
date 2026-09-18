"""Explicit, auditable Issue-to-PR-to-CI-to-merge workflow."""
from __future__ import annotations

from dataclasses import dataclass, field

from github_ci import GitHubActions
from github_git import GitPublisher
from github_mode import GitHubClient, GitHubPermissionError
from github_pr import GitHubPullRequests
from core.diagnostics import from_exception
from github_workspace import GitHubWorkspace


@dataclass
class WorkflowState:
    issue: int
    branch: str = ""
    commit: str = ""
    pr: int | None = None
    ci_success: bool = False
    merged: bool = False
    phase: str = "issue"
    history: list[str] = field(default_factory=list)


class GitHubWorkflow:
    """Orchestration shell; it never grants capabilities or merges implicitly."""
    def __init__(self, client: GitHubClient, workspace: GitHubWorkspace, publisher: GitPublisher) -> None:
        self.client = client
        self.workspace = workspace
        self.publisher = publisher
        self.prs = GitHubPullRequests(client)
        self.actions = GitHubActions(client)

    def start(self, issue: int) -> WorkflowState:
        if issue < 1: raise ValueError("issue number must be positive")
        branch = self.workspace.branch_for_issue(issue)
        state = WorkflowState(issue=issue, branch=branch)
        state.history.append("issue")
        return state

    def record_commit(self, state: WorkflowState, commit_sha: str) -> None:
        if not commit_sha: raise ValueError("commit SHA is required")
        state.commit, state.phase = commit_sha, "commit"
        state.history.append("commit")

    def open_pr(self, state: WorkflowState, title: str, body: str = "") -> dict:
        if not state.commit: raise RuntimeError("commit is required before PR")
        pr = self.prs.create(title, state.branch, body=body)
        state.pr, state.phase = int(pr["number"]), "pr"
        state.history.append("pr")
        return pr

    def verify_ci(self, state: WorkflowState) -> bool:
        if not state.pr or not state.commit: raise RuntimeError("PR and commit are required before CI verification")
        runs = self.actions.runs_for_commit(state.commit)
        state.ci_success = self.actions.all_successful(runs)
        state.phase = "ci"
        state.history.append("ci")
        return state.ci_success

    def merge(self, state: WorkflowState, *, approved: bool = False, expected_head_sha: str | None = None) -> dict:
        if not approved: raise GitHubPermissionError("explicit merge approval is required")
        if not self.client.config.capabilities.allows("merge"): raise GitHubPermissionError("GitHub capability denied: merge")
        if not state.pr or not state.ci_success: raise RuntimeError("a PR with successful CI is required before merge")
        payload = {"merge_method":"squash"}
        if expected_head_sha: payload["sha"] = expected_head_sha
        result = self.client._request("PUT", f"repos/{self.client.config.repo_full_name}/pulls/{state.pr}/merge", capability="merge", payload=payload)
        if not result.get("merged"): raise RuntimeError(str(result.get("message", "merge was not completed")))
        state.merged, state.phase = True, "merged"
        state.history.append("merged")
        return result

    def audit_e2e_readiness(self) -> dict:
        """Safely audit the current environment readiness for live E2E GitHub execution."""
        has_token = bool(self.client.config.token)
        repo_full = self.client.config.repo_full_name
        capabilities = self.client.permissions_snapshot()
        remote_info = {}
        try:
            remote_info = self.publisher.preflight()
        except Exception as exc:
            remote_info = {"error": from_exception(exc, category="github").message}

        if not has_token:
            status = "NOT TESTED"
            rationale = "Live GitHub E2E execution skipped: GITHUB_TOKEN is not configured in environment."
        elif not repo_full:
            status = "FAIL"
            rationale = "GitHub repository identity (owner/repo) is not configured."
        elif not all(capabilities.values()):
            status = "PASS WITH LIMITATIONS"
            missing = [k for k, v in capabilities.items() if not v]
            rationale = f"Live GitHub token present, but missing capabilities: {', '.join(missing)}"
        else:
            status = "PASS"
            rationale = "Full GitHub E2E capabilities are configured and ready."

        return {
            "status": status,
            "rationale": rationale,
            "has_token": has_token,
            "repo_full_name": repo_full,
            "capabilities": capabilities,
            "remote": remote_info,
        }
