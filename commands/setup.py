from core.gemini_setup import GeminiSetupError, interactive_setup


class SetupCommand:
    def run(self, provider: str = "gemini"):
        if provider.lower() != "gemini":
            raise SystemExit("Usage: yasincoder setup gemini")
        try:
            return interactive_setup()
        except GeminiSetupError as exc:
            raise SystemExit(f"Gemini setup failed: {exc}") from exc
