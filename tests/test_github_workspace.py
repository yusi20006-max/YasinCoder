import unittest
from unittest.mock import Mock, patch

from github_workspace import GitWorkspace, issue_branch_name


class WorkspaceTests(unittest.TestCase):
    def test_issue_branch_name_is_deterministic_and_safe(self):
        self.assertEqual(issue_branch_name(12, "Fix: unsafe / paths!"), "issue/12-fix-unsafe-paths")

    def test_invalid_issue_number_rejected(self):
        with self.assertRaises(ValueError):
            issue_branch_name(0, "x")

    @patch("github_workspace.subprocess.run")
    def test_checkout_new_does_not_allow_force(self, run):
        workspace = GitWorkspace("/tmp/repo")
        with self.assertRaises(Exception):
            workspace.checkout_new("feature", force=True)
        run.assert_not_called()

    @patch("github_workspace.subprocess.run")
    def test_git_arguments_are_structured(self, run):
        run.return_value.returncode = 0
        run.return_value.stdout = "master\n"
        run.return_value.stderr = ""
        self.assertEqual(GitWorkspace("/tmp/repo").current_branch(), "master")
        args = run.call_args.args[0]
        self.assertEqual(args, ("git", "-C", "/tmp/repo", "branch", "--show-current"))


if __name__ == "__main__":
    unittest.main()
