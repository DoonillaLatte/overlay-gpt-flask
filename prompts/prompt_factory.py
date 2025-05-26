from typing import Dict, Type
from .prompt_strategy import PromptStrategy
from .strategies.explain_prompt import ExplainPrompt
from .strategies.freestyle_prompt import FreestylePrompt
from .strategies.generate_text_prompt import GenerateTextPrompt
from .strategies.summary_prompt import SummaryPrompt
from .strategies.convert_prompt import ConvertPrompt

class PromptFactory:
    def __init__(self):
        self._strategies: Dict[str, Type[PromptStrategy]] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        self.register_strategy("explain", ExplainPrompt)
        self.register_strategy("freestyle", FreestylePrompt)
        self.register_strategy("generate_text", GenerateTextPrompt)
        self.register_strategy("summary", SummaryPrompt)
        self.register_strategy("convert_prompt", ConvertPrompt)
        
    def register_strategy(self, name: str, strategy: Type[PromptStrategy]):
        self._strategies[name] = strategy
    
    def get_strategy(self, name: str) -> PromptStrategy:
        if name not in self._strategies:
            raise ValueError(f"Unknown prompt strategy: {name}")
        return self._strategies[name]()
