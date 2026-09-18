import unittest
from pathlib import Path


class ReleaseVersionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_version_is_consistent(self):
        version = (self.root / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "0.2.0")
        runtime = (self.root / "core" / "version.py").read_text(encoding="utf-8")
        self.assertIn('VERSION="0.2.0"', runtime)
        pyproject = (self.root / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('version = { file = "VERSION" }', pyproject)

    def test_changelog_and_release_docs_reference_release(self):
        changelog = (self.root / "CHANGELOG.md").read_text(encoding="utf-8")
        release = (self.root / "docs" / "RELEASE.md").read_text(encoding="utf-8")
        self.assertTrue(changelog.startswith("# Changelog\n\n## 0.2.0"))
        self.assertIn("0.2.0 release evidence boundaries", release)


if __name__ == "__main__":
    unittest.main()
