import unittest

from security import SecurityPolicy


class SecurityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = SecurityPolicy(
            api_key="secret",
            allowed_origins=("https://example.test",),
            max_body_bytes=4096,
        )

    def test_authentication_is_required_when_key_configured(self):
        self.assertFalse(self.policy.authenticate(None))
        self.assertFalse(self.policy.authenticate("wrong"))
        self.assertTrue(self.policy.authenticate("secret"))

    def test_origin_policy_is_allowlist(self):
        self.assertTrue(self.policy.origin_allowed(None))
        self.assertTrue(self.policy.origin_allowed("https://example.test"))
        self.assertFalse(self.policy.origin_allowed("https://evil.test"))

    def test_security_headers_do_not_leak_secrets(self):
        headers = self.policy.public_headers("https://example.test")
        self.assertNotIn("secret", str(headers))
        self.assertEqual(headers["Access-Control-Allow-Origin"], "https://example.test")


if __name__ == "__main__":
    unittest.main()
