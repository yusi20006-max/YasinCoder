import io
import os
import sys
import unittest
from contextlib import redirect_stdout
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
        output = io.StringIO()
        with patch.object(app, "dashboard"), redirect_stdout(output):
            with patch.object(sys.stdin, "isatty", return_value=False), patch.object(sys.stdout, "isatty", return_value=True):
                self.assertEqual(app.run(), 0)
        self.assertEqual(output.getvalue(), "")

    def test_no_color_disables_ansi(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(tui._supports_ansi())


if __name__ == "__main__":
    unittest.main()
