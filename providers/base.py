from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Provider contract shared by local and remote AI backends."""

    name = "base"

    @abstractmethod
    def chat(self, prompt: str) -> str:
        raise NotImplementedError

    def health(self) -> bool:
        return True

    def capabilities(self) -> dict:
        return {"chat": True, "streaming": False}
