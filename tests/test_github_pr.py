import unittest
from unittest.mock import Mock

from github_mode import GitHubCapabilities, GitHubClient, GitHubConfig, GitHubPermissionError
from github_pr import GitHubPullRequests


class PRTests(unittest.TestCase):
    def make(self, pr_write=False):
        client = GitHubClient(GitHubConfig(owner="o", repo="r", token="x", capabilities=GitHubCapabilities(pr_write=pr_write)))
        client._request = Mock(return_value={"number": 4, "html_url": "https://github.com/o/r/pull/4", "state": "open", "head": {"ref": "feature"}, "base": {"ref": "master"}})
        return client, GitHubPullRequests(client)

    def test_create_requires_pr_write(self):
        _, prs = self.make(False)
        with self.assertRaises(GitHubPermissionError):
            # Exercise the real client path rather than the mocked request.
            client = GitHubClient(GitHubConfig(owner="o", repo="r", token="x"))
            GitHubPullRequests(client).create("x", "feature")

    def test_create_uses_head_and_base(self):
        client, prs = self.make(True)
        prs.create("Title", "feature", "master", "Body")
        client._request.assert_called_once_with("POST", "repos/o/r/pulls", capability="pr_write", payload={"title":"Title","head":"feature","base":"master","body":"Body"})

    def test_summary_extracts_refs(self):
        _, prs = self.make(True)
        summary = prs.summary(prs.get(4))
        self.assertEqual(summary.head, "feature")
        self.assertEqual(summary.base, "master")
        self.assertEqual(summary.number, 4)


if __name__ == "__main__":
    unittest.main()
