import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from core.runtime import cache_dir, command_available, config_dir, detect_runtime, find_command, run_command, user_data_dir


class PlatformIntegrationTests(unittest.TestCase):
    def test_runtime_detection_and_family_are_normalized(self):
        runtime = detect_runtime()
        self.assertTrue(runtime.system)
        self.assertTrue(runtime.machine)
        self.assertTrue(runtime.python)
        self.assertIn(runtime.family, {"termux", "wsl", "windows", "linux", "macos", "other"})

    def test_native_user_directories_are_paths(self):
        self.assertIsInstance(user_data_dir(), Path)
        self.assertIsInstance(config_dir(), Path)
        self.assertIsInstance(cache_dir(), Path)

    def test_command_discovery_uses_path(self):
        self.assertTrue(find_command(Path(sys.executable).name) or find_command("python"))
        self.assertTrue(command_available(Path(sys.executable).name, "python"))

    def test_direct_process_execution_is_shell_independent(self):
        result = run_command([sys.executable, "-c", "print('platform-ok')"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "platform-ok")
        self.assertEqual(result.stderr, "")

    def test_platform_specific_directory_mapping(self):
        with patch("core.runtime.detect_runtime") as detect:
            detect.return_value = type("Runtime", (), {"system": "Windows", "is_termux": False, "is_wsl": False})()
            self.assertIn("AppData", str(user_data_dir()))
            self.assertIn("AppData", str(config_dir()))
            self.assertIn("AppData", str(cache_dir()))

            detect.return_value = type("Runtime", (), {"system": "Darwin", "is_termux": False, "is_wsl": False})()
            self.assertIn("Library", str(user_data_dir()))
            self.assertIn("Library", str(config_dir()))
            self.assertIn("Library", str(cache_dir()))


if __name__ == "__main__":
    unittest.main()
