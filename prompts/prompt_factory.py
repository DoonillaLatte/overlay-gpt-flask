from typing import Dict, Type
from .prompt_strategy import PromptStrategy
from .strategies.explain_prompt import ExplainPrompt
from .strategies.freestyle_prompt import FreestylePrompt
from .strategies.generate_text_prompt import GenerateTextPrompt
from .strategies.summary_prompt import SummaryPrompt
from .strategies.ppt_style_prompt import PPTStylePrompt
from .strategies.word_style_prompt import WordStylePrompt

class PromptFactory:
    def __init__(self):
        self._strategies: Dict[str, Type[PromptStrategy]] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        self.register_strategy("explain", ExplainPrompt)
        self.register_strategy("freestyle", FreestylePrompt)
        self.register_strategy("generate_text", GenerateTextPrompt)
        self.register_strategy("summary", SummaryPrompt)
        self.register_strategy("ppt_style", PPTStylePrompt)
        self.register_strategy("word_style", WordStylePrompt)
        
    def register_strategy(self, name: str, strategy: Type[PromptStrategy]):
        self._strategies[name] = strategy
    
    def get_strategy(self, name: str) -> PromptStrategy:
        if name not in self._strategies:
            raise ValueError(f"Unknown prompt strategy: {name}")
        return self._strategies[name]()
