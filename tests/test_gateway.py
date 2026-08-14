import json
import unittest
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

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
        self.last_routing = {"selected": "fake-local", "attempts": [{"model": "fake-local", "outcome": "success"}], "offline": True}

    def list_models(self):
        return self.models.list()

    def ask(self, prompt, model_name=None):
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

    def post(self, path, payload):
        request = Request(
            self.base + path,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        return urlopen(request)

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
        with self.post("/v1/chat/completions", {
            "model": "fake-local",
            "messages": [{"role": "user", "content": "hello"}],
        }) as response:
            data = json.load(response)
            self.assertEqual(data["object"], "chat.completion")
            self.assertEqual(data["model"], "fake-local")
            self.assertEqual(data["choices"][0]["message"]["content"], "reply:hello")
            self.assertIn("routing", data)

    def test_invalid_message_schema(self):
        with self.assertRaises(HTTPError) as raised:
            self.post("/v1/chat/completions", {"messages": [{"content": "hello"}]})
        self.assertEqual(raised.exception.code, 400)
        body = json.loads(raised.exception.read())
        self.assertEqual(body["error"]["code"], "invalid_request")

    def test_unknown_model(self):
        with self.assertRaises(HTTPError) as raised:
            self.post("/v1/chat/completions", {
                "model": "missing",
                "messages": [{"role": "user", "content": "hello"}],
            })
        self.assertEqual(raised.exception.code, 404)
        body = json.loads(raised.exception.read())
        self.assertEqual(body["error"]["code"], "model_not_found")

    def test_compatibility_endpoint_matches_contract(self):
        with self.post("/api/chat", {
            "model": "fake-local",
            "messages": [{"role": "user", "content": "hello"}],
        }) as response:
            data = json.load(response)
            self.assertEqual(data["object"], "chat.completion")
            self.assertEqual(data["choices"][0]["message"]["role"], "assistant")


if __name__ == "__main__":
    unittest.main()
