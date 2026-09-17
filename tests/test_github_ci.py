import unittest
from unittest.mock import Mock

from github_ci import CIRun, GitHubActions
from github_mode import GitHubCapabilities, GitHubClient, GitHubConfig


class CITests(unittest.TestCase):
    def test_runs_are_normalized(self):
        client = GitHubClient(GitHubConfig(owner="o", repo="r", token="x", capabilities=GitHubCapabilities(read=True)))
        client._request = Mock(return_value={"workflow_runs":[{"id":1,"name":"tests","status":"completed","conclusion":"success","html_url":"u","head_sha":"abcdef1"}]})
        runs = GitHubActions(client).runs_for_commit("abcdef1")
        self.assertEqual(runs[0], CIRun(1,"tests","completed","success","u","abcdef1"))

    def test_invalid_sha_rejected(self):
        client = GitHubClient(GitHubConfig(owner="o", repo="r", token="x", capabilities=GitHubCapabilities(read=True)))
        with self.assertRaises(ValueError): GitHubActions(client).runs_for_commit("not-a-sha")

    def test_failure_and_success_helpers(self):
        runs = [CIRun(1,"a","completed","success","",""), CIRun(2,"b","completed","failure","","")]
        self.assertEqual(len(GitHubActions.failed(runs)), 1)
        self.assertFalse(GitHubActions.all_successful(runs))


if __name__ == "__main__":
    unittest.main()
