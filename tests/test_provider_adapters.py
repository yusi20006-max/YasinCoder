import json
import urllib.error
import unittest
from unittest.mock import patch

from providers.base import ProviderAuthenticationError, ProviderUnavailable
from providers.factory import create_adapter
from providers.llama_cpp import LlamaCppAdapter
from providers.ollama import OllamaAdapter
from providers.http_compatible import OpenAICompatibleAdapter


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
    def test_factory_selects_local_adapters(self):
        llama = create_adapter({"name": "local", "type": "llama_cpp", "base_url": "http://local", "model": "m"})
        ollama = create_adapter({"name": "local", "type": "ollama", "base_url": "http://local", "model": "m"})
        self.assertIsInstance(llama, LlamaCppAdapter)
        self.assertIsInstance(ollama, OllamaAdapter)
        self.assertTrue(llama.offline and ollama.offline)

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

    def test_unavailable_error_does_not_expose_credentials(self):
        adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m", "api_key": "SECRET"})
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
            with self.assertRaises(ProviderUnavailable) as context:
                adapter.chat("hello")
        self.assertNotIn("SECRET", str(context.exception))


if __name__ == "__main__":
    unittest.main()
