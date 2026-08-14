import json
import unittest
from threading import Thread
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from gateway import create_server
from routing import RoutingError
from security import SecurityPolicy


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


class FailingManager(FakeManager):
    def ask(self, prompt, model_name=None):
        raise RoutingError("network", "provider unavailable")


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

    def request(self, path, method="GET", payload=None, headers=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = Request(self.base + path, data=data, method=method, headers=headers or {})
        return urlopen(request)

    def post(self, path, payload, headers=None):
        return self.request(path, "POST", payload, {"Content-Type": "application/json", **(headers or {})})

    def test_health(self):
        with self.request("/health") as response:
            self.assertEqual(response.status, 200)
            self.assertTrue(json.load(response)["ok"])

    def test_models(self):
        with self.request("/v1/models") as response:
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

    def test_static_shell_is_public(self):
        with self.request("/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.headers["Content-Type"])

    def test_options_does_not_require_api_key(self):
        with self.request("/v1/chat/completions", "OPTIONS", headers={"Origin": "https://app.example"}) as response:
            self.assertEqual(response.status, 204)

    def test_provider_failure_is_safe(self):
        server = create_server("127.0.0.1", 0, FailingManager())
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        try:
            request = Request(
                base + "/v1/chat/completions",
                data=json.dumps({"model": "fake-local", "messages": [{"role": "user", "content": "hello"}]}).encode(),
                headers={"Content-Type": "application/json"},
            )
            with self.assertRaises(HTTPError) as raised:
                urlopen(request)
            self.assertEqual(raised.exception.code, 503)
            body = json.loads(raised.exception.read())
            self.assertEqual(body["error"]["code"], "provider_network")
            self.assertNotIn("provider unavailable", body["error"].get("message", ""))
        finally:
            server.shutdown()
            server.server_close()


class GatewaySecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        policy = SecurityPolicy(api_key="test-secret", allowed_origins=("https://app.example",), max_body_bytes=128)
        cls.server = create_server("127.0.0.1", 0, FakeManager(), policy)
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_protected_route_requires_api_key(self):
        with self.assertRaises(HTTPError) as raised:
            urlopen(self.base + "/v1/models")
        self.assertEqual(raised.exception.code, 401)

    def test_wrong_origin_is_rejected(self):
        request = Request(self.base + "/v1/models", headers={"Origin": "https://evil.example"})
        with self.assertRaises(HTTPError) as raised:
            urlopen(request)
        self.assertEqual(raised.exception.code, 403)

    def test_allowed_origin_and_key_succeed(self):
        request = Request(
            self.base + "/v1/models",
            headers={"Origin": "https://app.example", "Authorization": "Bearer test-secret"},
        )
        with urlopen(request) as response:
            self.assertEqual(response.status, 200)

    def test_oversized_body_is_rejected(self):
        payload = {"model": "fake-local", "messages": [{"role": "user", "content": "x" * 512}]}
        request = Request(
            self.base + "/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer test-secret"},
        )
        with self.assertRaises(HTTPError) as raised:
            urlopen(request)
        self.assertEqual(raised.exception.code, 413)


if __name__ == "__main__":
    unittest.main()
