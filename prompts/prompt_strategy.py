from abc import ABC, abstractmethod

class PromptStrategy(ABC):
    @abstractmethod
    def register_prompt(self, text: str) -> str:
        pass
