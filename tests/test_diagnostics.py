import unittest

from core.diagnostics import diagnostic, from_exception


class DiagnosticTests(unittest.TestCase):
    def test_secret_is_redacted_and_output_is_bounded(self):
        secret = "sk-" + "x" * 32
        result = diagnostic("provider", secret, detail=secret, context={"token": secret})
        data = result.as_dict()
        self.assertNotIn(secret, str(data))
        self.assertLessEqual(len(data["message"]), 512)
        self.assertLessEqual(len(data["detail"]), 2048)

    def test_unknown_category_fails_closed_to_internal(self):
        result = diagnostic("not-a-category", "failure")
        self.assertEqual(result.category, "internal")

    def test_provider_exception_is_normalized(self):
        error = RuntimeError("Authorization: Bearer " + "x" * 24)
        result = from_exception(error, category="provider")
        self.assertEqual(result.category, "provider")
        self.assertNotIn("Bearer", result.message)

    def test_context_sensitive_values_are_redacted(self):
        result = diagnostic(
            "github",
            "workflow failed",
            context={"authorization": "secret-token-value", "status": 503},
        )
        self.assertNotIn("secret-token-value", result.detail)
        self.assertIn("503", result.detail)


if __name__ == "__main__":
    unittest.main()
