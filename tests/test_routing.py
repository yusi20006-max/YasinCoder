import unittest
import urllib.error

from routing import Router, RoutingError, classify_error


def http_error(code):
    return urllib.error.HTTPError("http://example", code, "error", {}, None)


class RoutingTests(unittest.TestCase):
    def test_transient_failure_falls_back_once(self):
        models = {
            "primary": {"name": "primary", "type": "openai_compatible", "fallbacks": ["backup"]},
            "backup": {"name": "backup", "type": "openai_compatible"},
        }
        calls = []

        def ask(model):
            calls.append(model["name"])
            if model["name"] == "primary":
                raise TimeoutError("timed out")
            return "ok"

        result = Router(models.get).run(models["primary"], ask)
        self.assertEqual(result.output, "ok")
        self.assertEqual(result.selected, "backup")
        self.assertEqual([a.outcome for a in result.attempts], ["timeout", "success"])
        self.assertEqual(calls, ["primary", "backup"])

    def test_quota_does_not_fallback(self):
        models = {
            "primary": {"name": "primary", "type": "openai_compatible", "fallbacks": ["backup"]},
            "backup": {"name": "backup", "type": "openai_compatible"},
        }
        calls = []

        def ask(model):
            calls.append(model["name"])
            raise http_error(429)

        with self.assertRaises(RoutingError) as caught:
            Router(models.get).run(models["primary"], ask)

        self.assertEqual(caught.exception.kind, "quota")
        self.assertEqual(len(caught.exception.attempts), 1)
        self.assertEqual(calls, ["primary"])

    def test_fallback_chain_is_loop_free(self):
        models = {
            "a": {"name": "a", "fallbacks": ["b"]},
            "b": {"name": "b", "fallbacks": ["a"]},
        }
        self.assertEqual([m["name"] for m in Router(models.get).order(models["a"])], ["a", "b"])

    def test_offline_mode_never_adds_fallbacks(self):
        primary = {"name": "local", "offline": True, "fallbacks": ["cloud"]}
        calls = []

        def ask(model):
            calls.append(model["name"])
            raise TimeoutError("offline local unavailable")

        with self.assertRaises(RoutingError):
            Router(lambda name: {"name": name}).run(primary, ask)
        self.assertEqual(calls, ["local"])

    def test_error_classification(self):
        self.assertEqual(classify_error(http_error(429)), "quota")
        self.assertEqual(classify_error(http_error(401)), "auth")
        self.assertEqual(classify_error(http_error(503)), "server")
        self.assertEqual(classify_error(http_error(404)), "model")


if __name__ == "__main__":
    unittest.main()
