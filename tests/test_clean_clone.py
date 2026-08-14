import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def tracked_files():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


class CleanCloneTests(unittest.TestCase):
    def test_required_project_contract_files_exist(self):
        required = (
            "README.md",
            "LICENSE",
            "config.example",
            "docs/ARCHITECTURE.md",
            "docs/CONFIGURATION.md",
            "docs/GATEWAY.md",
            "gateway.py",
            "providers",
            "routing.py",
            "security.py",
            "tests",
        )
        for relative in required:
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).exists(), relative)

    def test_tracked_tree_contains_no_bundled_model_weights(self):
        forbidden_suffixes = {".gguf", ".safetensors", ".bin"}
        forbidden_fragments = ("qwen3-1.7b", "qwen3-local", "llama-server")

        for path in tracked_files():
            self.assertNotIn(path.suffix.lower(), forbidden_suffixes, str(path))
            self.assertFalse(
                any(fragment in path.name.lower() for fragment in forbidden_fragments),
                str(path),
            )

    def test_tracked_source_has_no_developer_runtime_paths(self):
        banned_paths = (
            "/data/data/com.termux/files/home/",
            "/data/data/com.termux/files/usr/",
        )
        source_suffixes = {".py", ".sh", ".yml", ".yaml", ".json", ".toml"}

        for path in tracked_files():
            if path.suffix.lower() not in source_suffixes:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for banned in banned_paths:
                self.assertNotIn(banned, text, str(path))

    def test_runtime_configuration_is_externalized(self):
        config_example = (ROOT / "config.example").read_text(encoding="utf-8")
        self.assertIn("YASIN_MODEL", config_example)
        self.assertIn("YASIN_BASE_URL", config_example)
        self.assertIn("YASIN_API_KEY", config_example)


if __name__ == "__main__":
    unittest.main()
