from abc import ABC, abstractmethod

class PromptStrategy(ABC):
    @abstractmethod
    def generate_prompt(self, text: str) -> str:
        pass
