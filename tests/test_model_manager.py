import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from models.manager import ModelManager, ModelValidationError


class ModelManagerTests(unittest.TestCase):
    def test_registry_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.json"
            manager = ModelManager(path)
            self.assertEqual(manager.list(), [])
            manager.upsert({
                "name": "my-local",
                "type": "openai_compatible",
                "base_url": "http://127.0.0.1:9999",
                "model": "my-model",
                "aliases": ["local"],
                "temperature": 0.1,
                "max_tokens": 1000,
            })
            self.assertEqual(manager.get("local")["model"], "my-model")
            manager.select("local")
            self.assertEqual(manager.default()["name"], "my-local")
            reloaded = ModelManager(path)
            self.assertEqual(reloaded.default()["name"], "my-local")
            self.assertEqual(json.loads(path.read_text())["default"], "my-local")
            self.assertTrue(reloaded.remove("local"))
            self.assertIsNone(reloaded.default())

    def test_secrets_are_rejected_from_persistence(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ModelManager(Path(tmp) / "models.json")
            with self.assertRaises(ModelValidationError):
                manager.upsert({"name": "bad", "type": "openai", "api_key": "super-secret"})
            self.assertFalse((Path(tmp) / "models.json").exists())

    def test_secret_environment_reference_is_resolved_only_at_runtime(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"TEST_YASIN_KEY": "super-secret"}):
            path = Path(tmp) / "models.json"
            manager = ModelManager(path)
            manager.upsert({"name": "remote", "type": "openai", "base_url": "https://example.invalid/v1", "model": "demo", "api_key_env": "TEST_YASIN_KEY"})
            raw = path.read_text()
            self.assertNotIn("super-secret", raw)
            self.assertEqual(manager.get("remote").get("api_key"), None)
            self.assertEqual(manager.resolve_secrets(manager.get("remote"))["api_key"], "super-secret")

    def test_environment_model_and_alias_select_deterministically(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ModelManager(Path(tmp) / "models.json")
            manager.upsert({"name": "zeta", "type": "ollama", "model": "z"})
            manager.upsert({"name": "alpha", "type": "ollama", "model": "a", "aliases": ["preferred"]})
            with patch.dict(os.environ, {"YASIN_MODEL": "preferred"}):
                self.assertEqual(manager.default()["name"], "alpha")
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("YASIN_MODEL", None)
                manager.data["default"] = ""
                self.assertEqual(manager.default()["name"], "alpha")

    def test_invalid_configuration_is_actionable(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ModelManager(Path(tmp) / "models.json")
            cases = [
                ({"name": "x", "type": "unknown"}, "unsupported provider type"),
                ({"name": "x", "type": "ollama", "max_tokens": 0}, "max_tokens"),
                ({"name": "x", "type": "ollama", "api_token": "secret"}, "secret value"),
            ]
            for model, message in cases:
                with self.subTest(model=model):
                    with self.assertRaisesRegex(ModelValidationError, message):
                        manager.upsert(model)


if __name__ == "__main__":
    unittest.main()
