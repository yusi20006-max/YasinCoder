import json
import urllib.error
import unittest
from unittest.mock import patch

from providers.base import (
    ProviderAdapter,
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderRequestError,
    ProviderUnavailable,
)
from providers.cloudflare import CloudflareProvider
from providers.factory import create_adapter
from providers.http_compatible import OpenAICompatibleAdapter
from providers.llama_cpp import LlamaCppAdapter
from providers.ollama import OllamaAdapter


class Response:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


class ProviderAdapterTests(unittest.TestCase):
    def assert_contract(self, adapter):
        self.assertIsInstance(adapter, ProviderAdapter)
        self.assertTrue(adapter.name)
        self.assertTrue(adapter.model_name)
        info = adapter.info()
        self.assertEqual(info.name, adapter.name)
        self.assertEqual(info.provider, adapter.provider_type)
        self.assertEqual(info.model, adapter.model_name)
        self.assertIsInstance(info.capabilities, tuple)
        self.assertIn("chat", info.capabilities)

    def test_factory_selects_all_supported_adapters(self):
        cases = [
            ({"name": "llama", "type": "llama_cpp", "base_url": "http://local", "model": "m"}, LlamaCppAdapter, True),
            ({"name": "ollama", "type": "ollama", "base_url": "http://local", "model": "m"}, OllamaAdapter, True),
            ({"name": "remote", "type": "openai_compatible", "base_url": "http://remote", "model": "m"}, OpenAICompatibleAdapter, False),
            ({"name": "gemini", "type": "gemini", "base_url": "http://gemini/v1", "model": "gemini-2.5-flash"}, OpenAICompatibleAdapter, False),
            ({"name": "cf", "type": "cloudflare", "account_id": "a", "api_token": "t", "model": "m"}, CloudflareProvider, False),
        ]
        for model, expected_type, offline in cases:
            with self.subTest(model=model["type"]):
                adapter = create_adapter(model)
                self.assertIsInstance(adapter, expected_type)
                self.assertIs(adapter.offline, offline)
                self.assert_contract(adapter)
                if model["type"] == "gemini":
                    self.assertEqual(adapter.provider_type, "gemini")

    def test_factory_rejects_unknown_provider(self):
        with self.assertRaises(ProviderConfigurationError):
            create_adapter({"name": "bad", "type": "unknown"})

    def test_openai_base_url_with_v1_is_not_double_prefixed(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote/v1", "model": "m"})
        with patch("urllib.request.urlopen", return_value=Response({"data": [{"id": "m"}]})) as mocked:
            self.assertEqual(adapter.list_models(), ["m"])
        self.assertEqual(mocked.call_args.args[0].full_url, "http://remote/v1/models")

    def test_openai_compatible_model_discovery_and_validation(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m"})
        with patch("urllib.request.urlopen", return_value=Response({"data": [{"id": "m"}, {"id": "other"}]})):
            self.assertEqual(adapter.list_models(), ["m", "other"])
            self.assertTrue(adapter.validate_model())

    def test_openai_compatible_chat_normalizes_response(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m"})
        with patch("urllib.request.urlopen", return_value=Response({"choices": [{"message": {"content": "ok"}}]})):
            self.assertEqual(adapter.chat("hello"), "ok")

    def test_openai_compatible_auth_error_is_normalized(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m"})
        error = urllib.error.HTTPError("http://remote", 401, "unauthorized", {}, None)
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ProviderAuthenticationError):
                adapter.chat("hello")

    def test_openai_compatible_empty_response_is_normalized(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m"})
        with patch("urllib.request.urlopen", return_value=Response({"choices": []})):
            with self.assertRaises(ProviderRequestError):
                adapter.chat("hello")

    def test_unavailable_error_does_not_expose_credentials(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m", "api_key": "SECRET"})
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            with self.assertRaises(ProviderUnavailable) as context:
                adapter.chat("hello")
        self.assertNotIn("SECRET", str(context.exception))

    def test_ollama_contract_and_chat(self):
        adapter = OllamaAdapter({"name": "ollama", "type": "ollama", "base_url": "http://local", "model": "m"})
        self.assert_contract(adapter)
        with patch("urllib.request.urlopen", return_value=Response({"response": "ok"})):
            self.assertEqual(adapter.chat("hello"), "ok")

    def test_ollama_discovery_and_validation(self):
        adapter = OllamaAdapter({"name": "ollama", "type": "ollama", "base_url": "http://local", "model": "m"})
        with patch("urllib.request.urlopen", return_value=Response({"models": [{"name": "m"}, {"name": "other"}]})):
            self.assertEqual(adapter.list_models(), ["m", "other"])
            self.assertTrue(adapter.validate_model())

    def test_cloudflare_contract_and_chat(self):
        adapter = CloudflareProvider({"name": "cf", "type": "cloudflare", "account_id": "a", "api_token": "t", "model": "m"})
        self.assert_contract(adapter)
        with patch("urllib.request.urlopen", return_value=Response({"result": {"response": "ok"}})):
            self.assertEqual(adapter.chat("hello"), "ok")


if __name__ == "__main__":
    unittest.main()
