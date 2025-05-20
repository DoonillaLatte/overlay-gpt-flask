from prompts.base import PromptStrategy
from registry import register_prompt
from typing import Optional

@register_prompt("question")
class QuestionPrompt(PromptStrategy):
    def __init__(self, prefix: Optional[str] = None, suffix: Optional[str] = None,
                  example: Optional[str] = None):
        self.prefix = prefix or (
            "당신은 전문적인 질문 답변 도우미입니다.\n\n"
            "당신의 임무는 다음과 같습니다:\n"
            "1. 주어진 질문의 요점을 파악하세요.\n"
            "2. 파악한 요점을 따라 정확하게 답변하세요.\n"
            "3. 가능하다면, 신뢰할 수 있는 출처나 일반적으로 알려진 정보 기준으로 설명하세요.\n"
            "4. 질문이 모호할 경우, 가능한 해석을 먼저 언급한 후 일반적인 방향으로 답변하세요.\n"
            "5. 문단을 나누고 명확하게 항목을 구분하세요."
            "6. 현재 받은 질문에 대해 존대말로 정중하게 답변하세요.\n\n"
            "Answer this: "
        )
        self.suffix = suffix or "Answer: "
        self.example = example 
        
        

    def generate_prompt(self, text: str) -> str:
        
        #로직 구현
        example_part = f"\n\n예시:\n{self.example}" if self.example else ""
        return f"""{self.prefix}\n\n{text}{example_part}\n\n{self.suffix}"""
    
