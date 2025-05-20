from prompts.base import PromptStrategy
from registry import register_prompt
from typing import Optional

@register_prompt("freestyle")
class FreestylePrompt(PromptStrategy):
    def __init__(self, prefix: Optional[str] = None, suffix: Optional[str] = None, example: Optional[str] = None):
        self.prefix = prefix or (
            "당신은 사용자의 주제나 질문에 대해 전문적인인 의견을 제시하는 역할입니다.\n\n"
            "다음 지침을 따르세요:\n"
            "1. 주어진 내용을 이해하고, 다양한 관점에서 자유롭게 사고합니다.\n"
            "2. 개인적인 의견, 창의적인 아이디어가 허용됩니다.\n"
            "3. 전문적인 지식이 필요할 경우 명확하게 설명하거나 유추합니다.\n"
            "4. 문장 구조는 유연하되, 읽기 쉽게 구성하세요.\n"
            "5. 질문이 명확하지 않더라도 자유롭게 해석해도 좋습니다.\n\n"
            "다음에 대해 자유롭게 답변해주세요:"
        )
        self.suffix = suffix or "당신의 생각: "
        self.example = example

    def generate_prompt(self, text: str) -> str:
        example_part = f"\n\n예시:\n{self.example}" if self.example else ""
        return f"""{self.prefix}

{text}{example_part}

{self.suffix}"""
