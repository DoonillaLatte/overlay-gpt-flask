from prompts.base import PromptStrategy
from registry import register_prompt
from typing import Optional

@register_prompt("summary")
class SummaryPrompt(PromptStrategy):
    def __init__(self, prefix: Optional[str] = None,suffix: Optional[str] = None,
                  example: Optional[str] = None):
        self.prefix = prefix or (
            "당신은 전문적인 요약 도우미입니다.\n\n"
            "당신의 임무는 다음과 같습니다:\n"
            "1. 주어진 내용을 왜곡 없이 핵심만 간결하게 요약하세요.\n"
            "2. 작성자의 어투와 표현 스타일을 최대한 유지하세요.\n"
            "3. 글의 목적과 용도를 고려해, 본문의 핵심 의도가 잘 드러나도록 요약하세요.\n"
            "4. 중복된 표현이나 불필요한 수식어는 제거하세요.\n"
            "5. 글이 뉴스, 설명문, 회의록, 에세이 중 어떤 유형인지 판단하여 그에 맞게 요약 방식과 어조를 조정하세요.\n"
            "6. 요약은 3~5문장 이내로 구성하되, 핵심 정보가 빠지지 않도록 하세요.\n\n"
            "Summarize this:"
        )
        self.suffix = suffix or "Summary: "
        self.example = example

    def generate_prompt(self, text: str) -> str:
        #로직 구현
        example_part = f"\n\n예시:\n{self.example}" if self.example else ""
        return f"""{self.prefix}\n\n{text}{example_part}\n\n{self.suffix}"""
