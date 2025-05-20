from prompts.base import PromptStrategy
from registry import register_prompt
from typing import Optional

@register_prompt("generate_text")
class GenerateTextPrompt(PromptStrategy):
    def __init__(
        self, 
        prefix: Optional[str] = None, 
        suffix: Optional[str] = None, 
        tone: Optional[str] = None,
        example: Optional[str] = None
    ):
        self.tone = tone or "전문문적"
        self.prefix = prefix or (
            f"당신은 {self.tone} 톤으로 텍스트를 생성하는 작가입니다.\n\n"
            "다음 지침을 따라 작성하세요:\n"
            "1. 주어진 주제에 맞는 문장을 구성하세요.\n"
            "2. 자연스럽고 논리적인 흐름을 유지하세요.\n"
            "3. 창의적이고 구체적인 내용을 포함하면 좋습니다.\n"
            "4. 문장은 깔끔하고 오탈자가 없어야 합니다.\n"
            "5. 텍스트의 목적이나 의도를 고려하여 적절한 스타일로 작성하세요.\n\n"
            "다음 주제를 바탕으로 텍스트를 작성하세요:"
        )
        self.suffix = suffix or "작성된 텍스트: "
        self.example = example

    def generate_prompt(self, text: str) -> str:
        example_part = f"\n\n예시:\n{self.example}" if self.example else ""
        return f"""{self.prefix}

{text}{example_part}

{self.suffix}"""
