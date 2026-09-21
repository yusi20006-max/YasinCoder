from core.gemini_setup import GeminiSetupError
from core.provider_setup import interactive_setup


class SetupCommand:
    def run(self, provider: str | None = None):
        if provider is None:
            try:
                return interactive_setup()
            except GeminiSetupError as exc:
                raise SystemExit(f"Gemini setup failed: {exc}") from exc
        if provider.lower() != "gemini":
            raise SystemExit("Usage: yasincoder setup [gemini]")
        try:
            from core.gemini_setup import interactive_setup as interactive_gemini_setup
            return interactive_gemini_setup()
        except GeminiSetupError as exc:
            raise SystemExit(f"Gemini setup failed: {exc}") from exc
