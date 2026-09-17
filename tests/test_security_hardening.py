import os
import tempfile
import unittest
from pathlib import Path

from core.agent_tools import execute
from core.redaction import redact
from core.sandbox import SandboxViolation, run_process, secure_tempdir, safe_path
from security import SecurityPolicy, credential_from_env


class SecurityHardeningTests(unittest.TestCase):
    def test_redaction_covers_known_token_shapes_and_sensitive_keys(self):
        text = "Authorization: Bearer super-secret-1234 sk-abcdefghijklmnop12"
        result = redact({"token": "top-secret-value", "message": text})
        self.assertEqual(result["token"], "[REDACTED]")
        self.assertNotIn("super-secret-1234", result["message"])
        self.assertNotIn("sk-abcdefghijklmnop12", result["message"])

    def test_credential_precedence_is_explicit(self):
        old = {name: os.environ.get(name) for name in ("YASIN_API_KEY", "YASIN_GATEWAY_API_KEY")}
        try:
            os.environ["YASIN_GATEWAY_API_KEY"] = "fallback"
            os.environ["YASIN_API_KEY"] = "primary"
            self.assertEqual(credential_from_env("YASIN_API_KEY", "YASIN_GATEWAY_API_KEY"), "primary")
        finally:
            for name, value in old.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def test_safe_path_rejects_traversal_and_external_symlink(self):
        with tempfile.TemporaryDirectory() as root, tempfile.TemporaryDirectory() as outside:
            root_path, outside_path = Path(root), Path(outside)
            (outside_path / "secret.txt").write_text("secret", encoding="utf-8")
            (root_path / "link").symlink_to(outside_path, target_is_directory=True)
            with self.assertRaises(SandboxViolation):
                safe_path("../outside.txt", root_path)
            with self.assertRaises(SandboxViolation):
                safe_path("link/secret.txt", root_path)

    def test_process_output_limit_fails_closed(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_process(["python", "-c", "print('x' * 10000)"], cwd=Path(root), max_output_bytes=1024)
            self.assertFalse(result["ok"])
            self.assertTrue(result["output_limited"])

    def test_shell_control_operators_are_rejected(self):
        result = execute("shell.exec", {"root": tempfile.gettempdir(), "command": "echo safe && touch escaped", "permissions": {"execute": True}})
        self.assertFalse(result["ok"])
        self.assertIn("control operators", result["error"])

    def test_secure_tempdir_cleans_up(self):
        with secure_tempdir() as directory:
            path = Path(directory)
            marker = path / "marker"
            marker.write_text("ok", encoding="utf-8")
            self.assertTrue(marker.exists())
        self.assertFalse(path.exists())

    def test_policy_error_output_does_not_include_api_key(self):
        policy = SecurityPolicy(api_key="secret-value")
        self.assertNotIn("secret-value", policy.safe_error("failed with secret-value"))


if __name__ == "__main__":
    unittest.main()
