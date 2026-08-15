import json
import tempfile
import unittest
from pathlib import Path

from memory import Memory


class MemoryTests(unittest.TestCase):
    def test_persistence_and_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Memory(tmp)
            item = first.add("project architecture", scope="project:a")
            first.add("other project", scope="project:b")
            second = Memory(tmp)
            self.assertEqual([item["id"]], [x["id"] for x in second.list(scope="project:a")])
            self.assertEqual(1, len(second.list(scope="project:b")))

    def test_retrieval_is_scored_and_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(tmp)
            first = memory.add("python architecture parser", scope="project:a")
            memory.add("python unrelated", scope="project:b")
            result = memory.retrieve("architecture parser", scope="project:a")
            self.assertEqual(first["id"], result[0]["id"])

    def test_secrets_are_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(tmp)
            item = memory.add("api_key=super-secret-value token=another-secret")
            self.assertNotIn("super-secret-value", item["text"])
            self.assertNotIn("another-secret", item["text"])
            raw = Path(tmp, "memory.json").read_text(encoding="utf-8")
            self.assertNotIn("super-secret-value", raw)

    def test_update_forget_and_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(tmp)
            item = memory.add("old", scope="session:1")
            self.assertIsNotNone(memory.update(item["id"], "new"))
            self.assertEqual("new", memory.list(scope="session:1")[0]["text"])
            self.assertEqual(1, memory.clear(scope="session:1"))
            self.assertEqual([], memory.list(scope="session:1"))

    def test_pruning_limits_items(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(tmp, max_items=3)
            for index in range(5):
                memory.add(f"item {index}")
            self.assertEqual(3, len(memory.list()))
            self.assertEqual("item 4", memory.list()[-1]["text"])


if __name__ == "__main__":
    unittest.main()
