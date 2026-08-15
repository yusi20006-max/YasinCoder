import tempfile
import unittest
from pathlib import Path

from core.test_generator import GENERATED_MARKER, TestGenerationError, TestGenerator, detect_framework


class TestGeneratorTests(unittest.TestCase):
    def make_project(self, root: Path):
        (root / "sample.py").write_text(
            "def add(left, right):\n    return left + right\n\nclass Calculator:\n    pass\n",
            encoding="utf-8",
        )

    def test_detect_python_framework_without_importing_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            self.assertEqual(detect_framework(root), ("python", "unittest"))

    def test_generation_is_marked_and_portable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            report = TestGenerator(root).generate()
            self.assertTrue(report.supported)
            generated = report.generated[0]
            text = generated.read_text(encoding="utf-8")
            self.assertIn(GENERATED_MARKER, text)
            self.assertIn("Path(__file__).parents[2]", text)
            self.assertIn("add", text)
            self.assertIn("Calculator", text)

    def test_user_test_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            user_test = root / "tests"
            user_test.mkdir()
            target = user_test / "test_sample.py"
            target.write_text("# USER TEST\n", encoding="utf-8")
            TestGenerator(root).generate()
            self.assertEqual(target.read_text(encoding="utf-8"), "# USER TEST\n")

    def test_generated_tests_execute_with_a_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_project(root)
            generator = TestGenerator(root)
            generator.generate()
            result = generator.run(timeout=30)
            self.assertTrue(result["ok"], result)
            self.assertTrue(result["generated"])

    def test_timeout_validation_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            generator = TestGenerator(tmp)
            with self.assertRaises(TestGenerationError):
                generator.run(timeout=601)


if __name__ == "__main__":
    unittest.main()
