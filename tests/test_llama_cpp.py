import os
import unittest
from unittest.mock import patch

from providers.llama_cpp import LlamaCppAdapter


class LlamaCppAdapterTests(unittest.TestCase):
    def test_default_max_tokens_is_conservative(self):
        adapter = LlamaCppAdapter({
            "name": "local",
            "type": "llama_cpp",
            "base_url": "http://127.0.0.1:18080",
            "model": "qwen",
        })
        self.assertEqual(adapter.model["max_tokens"], 512)

    def test_explicit_max_tokens_is_preserved_without_env_override(self):
        adapter = LlamaCppAdapter({
            "name": "local",
            "type": "llama_cpp",
            "base_url": "http://127.0.0.1:18080",
            "model": "qwen",
            "max_tokens": 1024,
        })
        self.assertEqual(adapter.model["max_tokens"], 1024)

    def test_environment_override_controls_local_budget(self):
        with patch.dict(os.environ, {"YASIN_LLAMA_MAX_TOKENS": "64"}):
            adapter = LlamaCppAdapter({
                "name": "local",
                "type": "llama_cpp",
                "base_url": "http://127.0.0.1:18080",
                "model": "qwen",
                "max_tokens": 4096,
            })
        self.assertEqual(adapter.model["max_tokens"], 64)


if __name__ == "__main__":
    unittest.main()
