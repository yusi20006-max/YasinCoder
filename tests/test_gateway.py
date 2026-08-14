import json
import unittest
from urllib.request import Request, urlopen
from threading import Thread

from gateway import create_server


class FakeModels:
    def list(self):
        return [{"name": "fake-local", "type": "openai_compatible", "capabilities": ["chat"], "default": True}]

    def get(self, name):
        return self.list()[0] if name == "fake-local" else None

    def default(self):
        return self.list()[0]


class FakeManager:
    def __init__(self):
        self.models = FakeModels()

    def list_models(self):
        return self.models.list()

    def ask(self, prompt):
        return f"reply:{prompt}"


class GatewayContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0, FakeManager())
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_health(self):
        with urlopen(self.base + "/health") as response:
            self.assertEqual(response.status, 200)
            self.assertTrue(json.load(response)["ok"])

    def test_models(self):
        with urlopen(self.base + "/v1/models") as response:
            data = json.load(response)
            self.assertEqual(data["data"][0]["id"], "fake-local")
            self.assertEqual(data["data"][0]["provider"], "openai_compatible")

    def test_chat_completions(self):
        request = Request(
            self.base + "/v1/chat/completions",
            data=json.dumps({
                "model": "fake-local",
                "messages": [{"role": "user", "content": "hello"}],
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request) as response:
            data = json.load(response)
            self.assertEqual(data["object"], "chat.completion")
            self.assertEqual(data["model"], "fake-local")
            self.assertEqual(data["choices"][0]["message"]["content"], "reply:hello")

    def test_unknown_model(self):
        request = Request(
            self.base + "/v1/chat/completions",
            data=json.dumps({
                "model": "missing",
                "messages": [{"role": "user", "content": "hello"}],
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(Exception):
            urlopen(request)


if __name__ == "__main__":
    unittest.main()
