import unittest
from unittest.mock import patch

from core.provider_setup import ProviderOption, select_provider


class ProviderSetupTests(unittest.TestCase):
    def test_down_and_enter_select_next_provider(self):
        options = (ProviderOption("gemini", "Gemini", True), ProviderOption("future", "Future", True))
        keys = iter(["down", "enter"])
        self.assertEqual(select_provider(options, key_reader=lambda: next(keys), output=lambda _: None), "future")

    def test_up_wraps_to_last_provider(self):
        options = (ProviderOption("first", "First", True), ProviderOption("second", "Second", True))
        keys = iter(["up", "enter"])
        self.assertEqual(select_provider(options, key_reader=lambda: next(keys), output=lambda _: None), "second")

    def test_unavailable_provider_cannot_be_selected(self):
        options = (ProviderOption("future", "Future", False), ProviderOption("gemini", "Gemini", True))
        keys = iter(["enter", "down", "enter"])
        output = []
        self.assertEqual(select_provider(options, key_reader=lambda: next(keys), output=output.append), "gemini")
        self.assertTrue(any("not implemented" in line for line in output))

    def test_escape_cancels(self):
        keys = iter(["esc"])
        self.assertIsNone(select_provider(key_reader=lambda: next(keys), output=lambda _: None))

    def test_setup_command_keeps_direct_gemini_compatibility(self):
        from commands.setup import SetupCommand
        with patch("commands.setup.interactive_gemini_setup", return_value={"name": "gemini"}) as setup:
            result = SetupCommand().run("gemini")
        setup.assert_called_once()
        self.assertEqual(result["name"], "gemini")

    def test_setup_command_dispatches_gateway_without_provider(self):
        from commands.setup import SetupCommand
        with patch("commands.setup.interactive_setup", return_value={"name": "gemini"}) as setup:
            result = SetupCommand().run()
        setup.assert_called_once()
        self.assertEqual(result["name"], "gemini")


if __name__ == "__main__":
    unittest.main()
