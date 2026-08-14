import json
import unittest
from unittest.mock import patch

from providers.local import LocalProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class LocalProviderTests(unittest.TestCase):
    @patch("providers.local.urllib.request.urlopen")
    def test_success(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"ok": True, "output": "QWEN_OK", "model": "qwen3-local", "offline": True}
        )
        result = LocalProvider().chat("Reply with QWEN_OK")
        self.assertEqual(result, "QWEN_OK")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:18765/api/qwen")

    @patch("providers.local.urllib.request.urlopen")
    def test_gateway_error(self, urlopen):
        urlopen.return_value = FakeResponse(
            {"ok": False, "error": "gateway unavailable"}
        )
        self.assertEqual(LocalProvider().chat("test"), "gateway unavailable")


if __name__ == "__main__":
    unittest.main()
