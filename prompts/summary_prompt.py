from prompts.base import PromptStrategy
from registry import register_prompt

@register_prompt("summary")
class SummaryPrompt(PromptStrategy):
    def generate_prompt(self, text: str) -> str:
        #로직 구현
        return f"Summarize this: {text}"
