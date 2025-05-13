from prompts.base import PromptStrategy
from registry import register_prompt

@register_prompt("question")
class QuestionPrompt(PromptStrategy):
    def generate_prompt(self, text: str) -> str:
        
        #로직 구현
        return f"Create a question about: {text}"
