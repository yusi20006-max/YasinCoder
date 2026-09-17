import os
import unittest
from unittest.mock import patch

import tui


class TuiUnitTests(unittest.TestCase):
    def test_clip_respects_width(self):
        self.assertEqual(tui._clip("abcdef", 4), "abc…")
        self.assertEqual(tui._clip("abc", 4), "abc")

    def test_terminal_size_has_safe_minimum(self):
        with patch("tui.shutil.get_terminal_size", return_value=os.terminal_size((20, 5))):
            self.assertEqual(tui._terminal_size(), (40, 12))

    def test_plain_mode_does_not_require_interactive_terminal(self):
        app = tui.YasinCoderTUI()
        with patch.object(app, "plain", return_value=None) as plain, patch("tui.sys.stdin.isatty", return_value=False), patch("tui.sys.stdout.isatty", return_value=True):
            self.assertEqual(app.run(), 0)
        plain.assert_called_once()

    def test_no_color_disables_ansi(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(tui._supports_ansi())

    def test_clip_handles_negative_or_zero_width(self):
        self.assertEqual(tui._clip("hello", 0), "")
        self.assertEqual(tui._clip("hello", -5), "")
        self.assertEqual(tui._clip("hello", 1), "h")

    def test_all_screens_render_without_error(self):
        app = tui.YasinCoderTUI()
        app.ansi = False
        app.dashboard()
        app.projects()
        app.sessions()
        app.models()
        app.git()
        app.system()
        app.settings()

    def test_tui_interactive_loop_commands(self):
        app = tui.YasinCoderTUI()
        inputs = iter(["1", "3", "5", "6", "8", "9", "m", "r", "n", "invalid", "q"])
        with patch("builtins.input", lambda prompt="": next(inputs)), patch("sys.stdin.isatty", return_value=True), patch("sys.stdout.isatty", return_value=True):
            res = app.run()
            self.assertEqual(res, 0)
            self.assertFalse(app.ansi)


if __name__ == "__main__":
    unittest.main()
