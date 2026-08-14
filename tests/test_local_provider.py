import unittest
from unittest.mock import patch

from providers.local import LocalProvider
from providers.manager import ProviderManager


class LocalProviderTests(unittest.TestCase):
    def test_openai_compatible_chat_contract(self):
        provider = LocalProvider(runtime="openai", base_url="http://127.0.0.1:18080", model="test-model")
        with patch.object(provider, "_request", return_value={"choices": [{"message": {"content": "OK"}}]}) as request:
            self.assertEqual(provider.chat("hello"), "OK")
            request.assert_called_once_with(
                "/v1/chat/completions",
                {"model": "test-model", "messages": [{"role": "user", "content": "hello"}]},
            )

    def test_ollama_chat_contract(self):
        provider = LocalProvider(runtime="ollama", base_url="http://127.0.0.1:11434", model="test-model")
        with patch.object(provider, "_request", return_value={"message": {"content": "OK"}}) as request:
            self.assertEqual(provider.chat("hello"), "OK")
            request.assert_called_once_with(
                "/api/chat",
                {"model": "test-model", "messages": [{"role": "user", "content": "hello"}], "stream": False},
            )

    def test_invalid_prompt_is_rejected(self):
        provider = LocalProvider()
        with self.assertRaises(ValueError):
            provider.chat("")

    def test_manager_selects_local_provider_from_environment(self):
        with patch.dict("os.environ", {"YASIN_AI_PROVIDER": "local"}):
            manager = ProviderManager()
            self.assertEqual(manager.default, "local")
            self.assertEqual(manager.get().name, "local")


if __name__ == "__main__":
    unittest.main()
