import io
import sys
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


class BareCommandTests(unittest.TestCase):
    def test_bare_command_prints_concise_summary(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["yasincoder"]), redirect_stdout(output):
            result = main.main()

        text = output.getvalue()
        self.assertIsNone(result)
        self.assertIn("YasinCoder", text)
        self.assertIn(main.VERSION, text)
        self.assertIn("ready", text)
        self.assertIn("yasincoder help", text)

    def test_bare_command_does_not_start_tui_or_provider(self):
        output = io.StringIO()
        with patch.object(sys, "argv", ["yasincoder"]),              patch("main.show"),              patch("main.HelpCommand.run", side_effect=AssertionError("help invoked")),              patch("main.ChatCommand.run", side_effect=AssertionError("chat invoked")),              redirect_stdout(output):
            main.main()

        self.assertIn("ready", output.getvalue())


if __name__ == "__main__":
    unittest.main()
