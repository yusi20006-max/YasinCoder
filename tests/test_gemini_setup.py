import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.gemini_setup import GeminiSetupError, discover_models, setup_gemini
from models.manager import ModelManager


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class GeminiSetupTests(unittest.TestCase):
    def test_setup_validates_key_discovers_model_and_selects_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "models.json"
            credential = Path(tmp) / "gemini.key"
            manager = ModelManager(registry)
            response = {"data": [{"id": "gemini-3.8-flash"}, {"id": "gemini-2.5-flash"}]}
            with patch.dict(os.environ, {"YASIN_GEMINI_CREDENTIAL_FILE": str(credential)}, clear=False), patch(
                "core.gemini_setup.urllib.request.urlopen", return_value=_Response(response)
            ):
                result = setup_gemini("TEST_GEMINI_KEY", manager)

            self.assertEqual(result["model"], "gemini-3.8-flash")
            self.assertEqual(manager.data["default"], "gemini")
            stored = manager.get("gemini")
            self.assertEqual(stored["type"], "gemini")
            self.assertEqual(stored["api_key_file"], str(credential))
            self.assertNotIn("api_key", stored)
            self.assertNotIn("api_key_file_env", stored)
            self.assertNotIn("TEST_GEMINI_KEY", registry.read_text())
            self.assertEqual(credential.read_text().strip(), "TEST_GEMINI_KEY")
            self.assertEqual(credential.stat().st_mode & 0o777, 0o600)

    def test_setup_persists_file_reference_for_fresh_manager_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = Path(tmp) / "models.json"
            credential = Path(tmp) / "gemini.key"
            response = {"data": [{"id": "gemini-3.8-flash"}]}
            with patch.dict(os.environ, {"YASIN_GEMINI_CREDENTIAL_FILE": str(credential)}, clear=False), patch(
                "core.gemini_setup.urllib.request.urlopen", return_value=_Response(response)
            ):
                setup_gemini("TEST_GEMINI_KEY", ModelManager(registry))

            fresh_manager = ModelManager(registry)
            persisted = fresh_manager.default()
            self.assertIsNotNone(persisted)
            resolved = fresh_manager.resolve_secrets(persisted)
            self.assertEqual(resolved["api_key"], "TEST_GEMINI_KEY")
            self.assertNotIn("TEST_GEMINI_KEY", registry.read_text())

    def test_missing_key_fails_before_network(self):
        with self.assertRaises(GeminiSetupError):
            discover_models("")

    def test_file_backed_key_resolves_without_storing_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            credential = Path(tmp) / "gemini.key"
            credential.write_text("FILE_KEY\n", encoding="utf-8")
            model = {"name": "gemini", "type": "gemini", "api_key_file": str(credential)}
            resolved = ModelManager.resolve_secrets(model)
            self.assertEqual(resolved["api_key"], "FILE_KEY")
            self.assertNotEqual(model.get("api_key"), "FILE_KEY")


if __name__ == "__main__":
    unittest.main()
