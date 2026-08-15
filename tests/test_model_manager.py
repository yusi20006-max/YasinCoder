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

    def test_discovery_finds_generic_endpoint_models_without_persisting_key(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"YASIN_BASE_URL": "https://example.invalid/v1", "YASIN_API_KEY": "SECRET"},
            clear=False,
        ):
            manager = ModelManager(Path(tmp) / "models.json")
            with patch.object(manager, "_json", return_value={"data": [{"id": "model-a"}, {"id": "model-b"}]}):
                found = manager.discover()
            self.assertEqual([item["model"] for item in found if item["type"] == "openai_compatible"], ["model-a", "model-b"])
            self.assertTrue(all("api_key" not in item for item in found))
            self.assertTrue(all(item.get("api_key_env") == "YASIN_API_KEY" for item in found if item["type"] == "openai_compatible"))

    def test_discovery_finds_gemini_and_uses_env_reference(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "SECRET", "GEMINI_MODEL": "gemini-test"},
            clear=False,
        ):
            manager = ModelManager(Path(tmp) / "models.json")
            with patch.object(manager, "_json", return_value={"data": [{"id": "gemini-test"}]}):
                found = manager.discover()
            gemini = [item for item in found if item["type"] == "gemini"]
            self.assertEqual(len(gemini), 1)
            self.assertEqual(gemini[0]["model"], "gemini-test")
            self.assertEqual(gemini[0]["api_key_env"], "GEMINI_API_KEY")
            self.assertNotIn("api_key", gemini[0])

    def test_discovery_finds_ollama_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = ModelManager(Path(tmp) / "models.json")
            def fake_json(base, path, *, timeout=3):
                if "11434" in base:
                    return {"models": [{"name": "qwen"}]}
                return None
            with patch.object(manager, "_json", side_effect=fake_json):
                found = manager.discover()
            self.assertEqual([(item["type"], item["model"]) for item in found], [("ollama", "qwen")])


if __name__ == "__main__":
    unittest.main()
