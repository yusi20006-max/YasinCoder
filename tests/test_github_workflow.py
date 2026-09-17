import unittest
from unittest.mock import Mock

from github_workflow import GitHubWorkflow
from github_mode import GitHubCapabilities, GitHubClient, GitHubConfig, GitHubPermissionError


class WorkflowTests(unittest.TestCase):
    def make(self):
        client = GitHubClient(GitHubConfig(owner="o", repo="r", token="x", capabilities=GitHubCapabilities(read=True, pr_write=True, merge=True)))
        workspace = Mock()
        workspace.branch_for_issue.return_value = "issue/1-fix"
        publisher = Mock()
        workflow = GitHubWorkflow(client, workspace, publisher)
        return client, workflow

    def test_start_records_issue_and_branch(self):
        _, workflow = self.make()
        state = workflow.start(1)
        self.assertEqual(state.branch, "issue/1-fix")
        self.assertEqual(state.history, ["issue"])

    def test_merge_requires_explicit_approval(self):
        _, workflow = self.make()
        state = workflow.start(1)
        state.pr, state.ci_success = 9, True
        with self.assertRaises(GitHubPermissionError): workflow.merge(state)

    def test_merge_requires_ci(self):
        _, workflow = self.make()
        state = workflow.start(1)
        state.pr = 9
        with self.assertRaises(RuntimeError): workflow.merge(state, approved=True)

    def test_merge_requires_capability(self):
        client, workflow = self.make()
        client.config = GitHubConfig(owner="o", repo="r", token="x", capabilities=GitHubCapabilities())
        state = workflow.start(1)
        state.pr, state.ci_success = 9, True
        with self.assertRaises(GitHubPermissionError): workflow.merge(state, approved=True)

    def test_full_e2e_workflow_sequence(self):
        client, workflow = self.make()
        workflow.prs.create = Mock(return_value={"number": 42})
        workflow.actions.runs_for_commit = Mock(return_value=[Mock(conclusion="success")])
        client._request = Mock(return_value={"merged": True})

        state = workflow.start(127)
        self.assertEqual(state.phase, "issue")

        workflow.record_commit(state, "abc123def456")
        self.assertEqual(state.commit, "abc123def456")
        self.assertEqual(state.phase, "commit")

        pr = workflow.open_pr(state, "Fix issue #127", "body")
        self.assertEqual(pr["number"], 42)
        self.assertEqual(state.pr, 42)
        self.assertEqual(state.phase, "pr")

        ci_ok = workflow.verify_ci(state)
        self.assertTrue(ci_ok)
        self.assertTrue(state.ci_success)
        self.assertEqual(state.phase, "ci")

        result = workflow.merge(state, approved=True, expected_head_sha="abc123def456")
        self.assertTrue(result["merged"])
        self.assertTrue(state.merged)
        self.assertEqual(state.phase, "merged")
        self.assertEqual(state.history, ["issue", "commit", "pr", "ci", "merged"])

    def test_audit_e2e_readiness_no_token(self):
        client = GitHubClient(GitHubConfig(owner="o", repo="r", token=""))
        publisher = Mock()
        publisher.preflight.return_value = {"branch": "master"}
        workflow = GitHubWorkflow(client, Mock(), publisher)
        audit = workflow.audit_e2e_readiness()
        self.assertEqual(audit["status"], "NOT TESTED")
        self.assertIn("GITHUB_TOKEN is not configured", audit["rationale"])

    def test_audit_e2e_readiness_full(self):
        client = GitHubClient(GitHubConfig(
            owner="o", repo="r", token="token123",
            capabilities=GitHubCapabilities(read=True, issue_write=True, branch_write=True, push=True, pr_write=True, merge=True)
        ))
        publisher = Mock()
        publisher.preflight.return_value = {"branch": "master"}
        workflow = GitHubWorkflow(client, Mock(), publisher)
        audit = workflow.audit_e2e_readiness()
        self.assertEqual(audit["status"], "PASS")
        self.assertTrue(audit["has_token"])


if __name__ == "__main__":
    unittest.main()
