import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_public_package_exists(self):
        package = ROOT / "yasincoder" / "__init__.py"
        self.assertTrue(package.is_file())

    def test_pyproject_declares_cli_and_package(self):
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('[project.scripts]', text)
        self.assertIn('yasincoder = "main:main"', text)
        self.assertIn('"yasincoder*"', text)
        self.assertIn('"models*"', text)

    def test_source_tree_import_smoke(self):
        result = subprocess.run(
            [sys.executable, "-c", "import yasincoder; assert yasincoder.__version__"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
