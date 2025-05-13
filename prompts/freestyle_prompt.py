from typing import Optional

class FreestylePrompt:
    def __init__(self, prefix: Optional[str] = None, suffix: Optional[str] = None):
        """
        프롬프트 생성을 위한 클래스 초기화
        
        Args:
            prefix (Optional[str]): 프롬프트 앞에 추가할 텍스트
            suffix (Optional[str]): 프롬프트 뒤에 추가할 텍스트
        """
        self.prefix = prefix or "다음 내용에 대해 자유롭게 답변해주세요:"
        self.suffix = suffix or "답변:"

    def generate_prompt(self, text: str) -> str:
        """
        주어진 텍스트를 기반으로 프롬프트를 생성합니다.
        
        Args:
            text (str): 프롬프트에 포함될 텍스트
            
        Returns:
            str: 생성된 프롬프트
        """
        return f"""{self.prefix}

{text}

{self.suffix}"""
