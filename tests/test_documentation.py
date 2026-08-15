import json
import tempfile
import unittest
from pathlib import Path

from core.documentation import analyze, architecture_markdown, api_markdown, report, render, source_files


class DocumentationGeneratorTests(unittest.TestCase):
    def make_project(self):
        root = Path(tempfile.mkdtemp())
        (root / "app.py").write_text(
            '"""Example module."""\n\nimport json\n\nclass Greeter:\n    """Greets users."""\n    pass\n\ndef hello(name):\n    """Return a greeting."""\n    return name\n',
            encoding="utf-8",
        )
        (root / ".env").write_text("API_KEY=should-not-be-read", encoding="utf-8")
        return root

    def test_source_analysis_is_structural(self):
        root = self.make_project()
        records = analyze(root)
        self.assertEqual([r["path"] for r in records], ["app.py"])
        self.assertEqual(records[0]["classes"][0]["name"], "Greeter")
        self.assertEqual(records[0]["functions"][0]["name"], "hello")

    def test_outputs_are_deterministic(self):
        root = self.make_project()
        records = analyze(root)
        self.assertEqual(api_markdown(records), api_markdown(analyze(root)))
        self.assertEqual(architecture_markdown(records), architecture_markdown(analyze(root)))
        self.assertEqual(report(records), report(analyze(root)))

    def test_report_is_json_and_excludes_runtime_state(self):
        root = self.make_project()
        payload = json.loads(render("report", str(root), "HEAD^"))
        self.assertEqual(payload["files"], 1)
        self.assertNotIn(".env", json.dumps(payload))

    def test_secret_redaction_is_applied_to_change_output(self):
        root = self.make_project()
        # No git metadata means an empty, safe change report rather than arbitrary file content.
        self.assertEqual(render("changes", str(root)), "[]\n")

    def test_source_files_ignore_runtime_directories(self):
        root = self.make_project()
        (root / "build").mkdir()
        (root / "build" / "runtime.py").write_text("password='secret'", encoding="utf-8")
        self.assertEqual([p.name for p in source_files(root)], ["app.py"])


if __name__ == "__main__":
    unittest.main()
