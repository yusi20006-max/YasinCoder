import json
import urllib.error
from unittest.mock import patch

import pytest

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


def test_factory_selects_local_adapters():
    llama = create_adapter({"name": "local", "type": "llama_cpp", "base_url": "http://local", "model": "m"})
    ollama = create_adapter({"name": "local", "type": "ollama", "base_url": "http://local", "model": "m"})
    assert isinstance(llama, LlamaCppAdapter)
    assert isinstance(ollama, OllamaAdapter)
    assert llama.offline and ollama.offline


def test_openai_compatible_chat_normalizes_response():
    adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m"})
    with patch("urllib.request.urlopen", return_value=Response({"choices": [{"message": {"content": "ok"}}]})):
        assert adapter.chat("hello") == "ok"


def test_openai_compatible_auth_error_is_normalized():
    adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m"})
    error = urllib.error.HTTPError("http://remote", 401, "unauthorized", {}, None)
    with patch("urllib.request.urlopen", side_effect=error):
        with pytest.raises(ProviderAuthenticationError):
            adapter.chat("hello")


def test_unavailable_error_does_not_expose_url_or_credentials():
    adapter = OpenAICompatibleAdapter({"name": "remote", "base_url": "http://remote", "model": "m", "api_key": "SECRET"})
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("offline")):
        with pytest.raises(ProviderUnavailable) as exc:
            adapter.chat("hello")
    assert "SECRET" not in str(exc.value)
