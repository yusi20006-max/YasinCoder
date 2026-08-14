import unittest

from core.gateway_contract import chat_response, error_response, validate_chat_request


class GatewaySchemaTests(unittest.TestCase):
    def test_valid_request(self):
        model, messages = validate_chat_request({
            "model": "local",
            "messages": [{"role": "user", "content": "hello"}],
        })
        self.assertEqual(model, "local")
        self.assertEqual(messages[0]["role"], "user")

    def test_invalid_request_type(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            validate_chat_request([])

    def test_message_limit(self):
        with self.assertRaisesRegex(ValueError, "at most 128"):
            validate_chat_request({"messages": [{"role": "user", "content": "x"}] * 129})

    def test_response_shape(self):
        response = chat_response(
            request_id="yasin-test",
            model="local",
            content="ok",
            created=1,
            routing={"selected": "local", "attempts": [], "offline": True},
        )
        self.assertEqual(response["object"], "chat.completion")
        self.assertEqual(response["choices"][0]["message"]["role"], "assistant")
        self.assertTrue(response["routing"]["offline"])

    def test_error_shape(self):
        self.assertEqual(
            error_response("invalid_request", "bad"),
            {"error": {"code": "invalid_request", "message": "bad"}},
        )


if __name__ == "__main__":
    unittest.main()
