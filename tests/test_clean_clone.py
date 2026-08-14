import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class CleanCloneProductionGate(unittest.TestCase):
    def test_required_release_files_exist(self):
        for name in ("README.md", "LICENSE", "VERSION", "pyproject.toml", "CHANGELOG.md"):
            self.assertTrue((ROOT / name).is_file(), name)

    def test_required_docs_exist(self):
        for name in ("ARCHITECTURE.md", "CONFIGURATION.md", "GATEWAY.md", "RELEASE.md", "PRODUCTION_AUDIT.md"):
            self.assertTrue((ROOT / "docs" / name).is_file(), name)

    def test_model_and_runtime_data_are_not_required_in_tree(self):
        forbidden_suffixes = {".gguf", ".safetensors"}
        forbidden_names = {".env"}
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            self.assertNotIn(path.name, forbidden_names)
            self.assertNotIn(path.suffix.lower(), forbidden_suffixes)

    def test_no_developer_absolute_path_is_hardcoded(self):
        forbidden = "/data/data/com.termux/files/home/"
        for path in ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(forbidden, text, str(path))

    def test_version_is_semver(self):
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        parts = version.split(".")
        self.assertEqual(len(parts), 3)
        self.assertTrue(all(part.isdigit() for part in parts))


if __name__ == "__main__":
    unittest.main()
