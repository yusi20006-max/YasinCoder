import os
import unittest
from unittest.mock import patch

import tui
from core.slash_commands import complete, parse


class TuiUnitTests(unittest.TestCase):
    def test_clip_respects_width(self):
        self.assertEqual(tui._clip("abcdef", 4), "abc…")
        self.assertEqual(tui._clip("abc", 4), "abc")

    def test_terminal_size_has_safe_minimum(self):
        with patch("tui.shutil.get_terminal_size", return_value=os.terminal_size((20, 5))):
            self.assertEqual(tui._terminal_size(), (40, 12))

    def test_plain_mode_does_not_require_interactive_terminal(self):
        app = tui.YasinCoderTUI()
        with patch.object(app, "plain", return_value=None) as plain, patch(
            "tui.sys.stdin.isatty", return_value=False
        ), patch("tui.sys.stdout.isatty", return_value=True):
            self.assertEqual(app.run(), 0)
        plain.assert_called_once()

    def test_plain_mode_accepts_redirected_output(self):
        app = tui.YasinCoderTUI()
        with patch.object(app, "plain", return_value=None) as plain, patch(
            "tui.sys.stdin.isatty", return_value=True
        ), patch("tui.sys.stdout.isatty", return_value=False):
            self.assertEqual(app.run(), 0)
        plain.assert_called_once()

    def test_no_color_disables_ansi(self):
        with patch.dict(os.environ, {"NO_COLOR": "1"}):
            self.assertFalse(tui._supports_ansi())

    def test_prompt_empty_enter_selects_action(self):
        keys = iter(["down", "enter"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("action", "project"))

    def test_prompt_types_text_and_submits(self):
        keys = iter(list("fix tests") + ["enter"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("task", "fix tests"))

    def test_prompt_backspace_and_cursor_editing(self):
        keys = iter(list("abc") + ["left", "backspace", "enter"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("task", "ac"))

    def test_prompt_escape_cancels(self):
        keys = iter(["esc"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("cancel", None))

    def test_prompt_ctrl_p_opens_command_palette(self):
        keys = iter(["ctrl_p"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("palette", None))

    def test_prompt_ctrl_c_requests_quit(self):
        keys = iter(["ctrl_c"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("quit", None))

    def test_command_palette_wraps_and_selects(self):
        keys = iter(["up", "enter"])
        app = tui.YasinCoderTUI(key_reader=lambda: next(keys))
        with patch.object(app, "header"), patch.object(app, "footer"), patch.object(app, "ansi", False):
            self.assertEqual(app.command_palette(), "quit")

    def test_task_failure_is_recovered(self):
        app = tui.YasinCoderTUI(key_reader=lambda: "enter")
        with patch("commands.autonomous.AutonomousCommand.run", side_effect=RuntimeError("boom")), patch.object(app, "_pause"):
            app.task("bad task")

    def test_slash_completion(self):
        self.assertEqual([c.name for c in complete("/mo")], ["/model"])
        self.assertEqual([c.name for c in complete("/r")], ["/review"])

    def test_slash_parse_preserves_arguments(self):
        command, argument = parse("/review src/main.py")
        self.assertIsNotNone(command)
        self.assertEqual(command.action, "review")
        self.assertEqual(argument, "src/main.py")

    def test_slash_unknown_is_not_command(self):
        command, argument = parse("/unknown thing")
        self.assertIsNone(command)
        self.assertEqual(argument, "/unknown thing")

    def test_prompt_tab_completes_slash_command(self):
        keys = iter(list("/mo") + ["tab", "enter"])
        session = tui.PromptSession(lambda: next(keys), lambda _: None)
        self.assertEqual(session.run(), ("task", "/model"))


if __name__ == "__main__":
    unittest.main()
