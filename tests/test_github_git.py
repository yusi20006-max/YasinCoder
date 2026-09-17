import unittest
from unittest.mock import Mock, patch

from github_git import GitPublisher, GitSafetyError
from github_mode import GitHubCapabilities, GitHubClient, GitHubConfig, GitHubPermissionError


class GitPublisherTests(unittest.TestCase):
    def client(self, push=False):
        return GitHubClient(GitHubConfig(owner="o", repo="r", token="x", capabilities=GitHubCapabilities(push=push)))

    def test_push_requires_capability(self):
        with self.assertRaises(GitHubPermissionError):
            GitPublisher("/tmp/repo", self.client()).push()

    @patch("github_git.subprocess.run")
    def test_commit_uses_structured_git_commands(self, run):
        run.side_effect = [
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="file.py\n", stderr=""),
            Mock(returncode=0, stdout="", stderr=""),
            Mock(returncode=0, stdout="abc\n", stderr=""),
        ]
        sha = GitPublisher("/tmp/repo", self.client(True)).commit("safe change")
        self.assertEqual(sha, "abc")
        self.assertEqual(run.call_args_list[0].args[0], ("git", "-C", "/tmp/repo", "add", "-A"))

    @patch("github_git.subprocess.run")
    def test_empty_staging_is_rejected(self, run):
        run.side_effect = [Mock(returncode=0, stdout="", stderr=""), Mock(returncode=0, stdout="", stderr="")]
        with self.assertRaises(GitSafetyError):
            GitPublisher("/tmp/repo", self.client(True)).commit("nothing")

    @patch("github_git.subprocess.run")
    def test_remote_mismatch_blocks_push(self, run):
        run.return_value = Mock(returncode=0, stdout="https://github.com/other/repo.git\n", stderr="")
        with self.assertRaises(GitSafetyError):
            GitPublisher("/tmp/repo", self.client(True)).push()


if __name__ == "__main__":
    unittest.main()
