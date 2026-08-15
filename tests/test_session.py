import tempfile
import unittest
from pathlib import Path

from core.session import MAX_CONTEXT_CHARS, MAX_MESSAGES, SessionManager


class SessionTests(unittest.TestCase):
    def test_create_save_restore_and_delete(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = SessionManager(Path(tmp))
            session = manager.create(provider="local", model="demo")
            session.add("user", "hello")
            session.add("assistant", "world")
            manager.save(session)

            restored = manager.get(session.id)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.provider, "local")
            self.assertEqual(restored.model, "demo")
            self.assertEqual([m["content"] for m in restored.messages], ["hello", "world"])
            self.assertTrue(manager.delete(session.id))
            self.assertIsNone(manager.get(session.id))

    def test_messages_are_bounded_and_secrets_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = SessionManager(Path(tmp))
            session = manager.create()
            for index in range(MAX_MESSAGES + 10):
                session.add("user", f"api_key=super-secret-{index}")
            self.assertLessEqual(len(session.messages), MAX_MESSAGES)
            self.assertNotIn("super-secret", session.messages[-1]["content"])
            self.assertLessEqual(sum(len(m["content"]) for m in session.messages), MAX_CONTEXT_CHARS)

    def test_invalid_session_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = SessionManager(Path(tmp))
            with self.assertRaises(ValueError):
                manager.get("../escape")


if __name__ == "__main__":
    unittest.main()
