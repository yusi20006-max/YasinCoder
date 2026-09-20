import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


class BareCliSummaryTests(unittest.TestCase):
    def test_bare_invocation_is_concise_and_non_interactive(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["yasincoder"]), patch("main.show") as show, redirect_stdout(output):
            main.main()

        self.assertEqual(output.getvalue().strip(), "YasinCoder 0.2.0 · ready")
        show.assert_not_called()

    def test_version_flag(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["yasincoder", "--version"]), patch("main.show") as show, redirect_stdout(output):
            main.main()

        self.assertEqual(output.getvalue().strip(), "YasinCoder 0.2.0")
        show.assert_not_called()

    def test_help_flag(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["yasincoder", "--help"]), patch("main.show") as show, redirect_stdout(output):
            main.main()

        self.assertIn("help", output.getvalue())
        self.assertIn("chat", output.getvalue())
        show.assert_not_called()

    def test_short_help_flag(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["yasincoder", "-h"]), patch("main.show") as show, redirect_stdout(output):
            main.main()

        self.assertIn("help", output.getvalue())
        show.assert_not_called()


if __name__ == "__main__":
    unittest.main()
