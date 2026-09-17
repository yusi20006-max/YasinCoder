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


    def test_open_pr_requires_recorded_commit(self):
        _, workflow = self.make()
        state = workflow.start(1)
        with self.assertRaises(RuntimeError): workflow.open_pr(state, "title")

    def test_verify_ci_requires_pr_and_commit(self):
        _, workflow = self.make()
        state = workflow.start(1)
        with self.assertRaises(RuntimeError): workflow.verify_ci(state)
        state.pr = 9
        with self.assertRaises(RuntimeError): workflow.verify_ci(state)


if __name__ == "__main__":
    unittest.main()
