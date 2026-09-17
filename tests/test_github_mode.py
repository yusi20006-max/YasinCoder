import json
import unittest
from unittest.mock import Mock

from github_mode import (
    GitHubAuthError,
    GitHubCapabilities,
    GitHubClient,
    GitHubConfig,
    GitHubPermissionError,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.payload


class GitHubModeTests(unittest.TestCase):
    def test_mutations_are_denied_by_default(self):
        client = GitHubClient(GitHubConfig(owner="o", repo="r", token="secret"))
        with self.assertRaises(GitHubPermissionError):
            client.create_issue("test")

    def test_read_requires_explicit_read_capability(self):
        opener = Mock(return_value=FakeResponse({"full_name": "o/r"}))
        config = GitHubConfig(owner="o", repo="r", token="secret", capabilities=GitHubCapabilities(read=True))
        client = GitHubClient(config, opener=opener)
        self.assertEqual(client.get_repo()["full_name"], "o/r")
        request = opener.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")
        self.assertEqual(client.audit_log[-1].path, "repos/o/r")

    def test_mutation_requires_token_even_when_capability_enabled(self):
        config = GitHubConfig(owner="o", repo="r", capabilities=GitHubCapabilities(issue_write=True))
        client = GitHubClient(config)
        with self.assertRaises(GitHubAuthError):
            client.create_issue("test")

    def test_redaction_never_exposes_token(self):
        config = GitHubConfig(token="super-secret", owner="o", repo="r", capabilities=GitHubCapabilities(read=True))
        client = GitHubClient(config)
        self.assertNotIn("super-secret", client._redact("Bearer super-secret failed"))
        self.assertIn("[REDACTED]", client._redact("Bearer super-secret failed"))

    def test_create_issue_sends_expected_payload(self):
        opener = Mock(return_value=FakeResponse({"number": 7}))
        config = GitHubConfig(owner="o", repo="r", token="secret", capabilities=GitHubCapabilities(issue_write=True))
        client = GitHubClient(config, opener=opener)
        self.assertEqual(client.create_issue("Hello", "Body")["number"], 7)
        request = opener.call_args.args[0]
        self.assertEqual(request.method, "POST")
        self.assertEqual(json.loads(request.data), {"title": "Hello", "body": "Body"})


if __name__ == "__main__":
    unittest.main()
