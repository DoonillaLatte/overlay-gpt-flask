from typing import Dict, Type
from .prompt_strategy import PromptStrategy
from .strategies.freestyle_text_prompt import FreestyleTextPrompt
from .strategies.modify_text_prompt import ModifyTextPrompt
from .strategies.freestyle_prompt import FreestylePrompt
from .strategies.generate_text_prompt import GenerateTextPrompt
from .strategies.check_spelling_prompt import CheckSpellingPrompt
from .strategies.convert_prompt import ConvertPrompt
from .strategies.convert_for_text_prompt import ConvertForTextPrompt

class PromptFactory:
    def __init__(self):
        self._strategies: Dict[str, Type[PromptStrategy]] = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        self.register_strategy("freestyle_text", FreestyleTextPrompt)
        self.register_strategy("freestyle", FreestylePrompt)
        self.register_strategy("generate_text", GenerateTextPrompt)
        self.register_strategy("modify_text", ModifyTextPrompt )
        self.register_strategy("check_spelling", CheckSpellingPrompt)
        self.register_strategy("convert", ConvertPrompt)
        self.register_strategy("convert_for_text", ConvertForTextPrompt)
        
    def register_strategy(self, name: str, strategy: Type[PromptStrategy]):
        self._strategies[name] = strategy
    
    def get_strategy(self, name: str) -> PromptStrategy:
        if name not in self._strategies:
            raise ValueError(f"Unknown prompt strategy: {name}")
        return self._strategies[name]()
