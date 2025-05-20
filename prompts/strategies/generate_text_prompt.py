from typing import Optional, Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
api_key = os.getenv("OPENAI_API_KEY")
from registry import register_prompt

@register_prompt("generate_text")
class GenerateTextPrompt():
    def __init__(self, user_input: Optional[str] = None, prefix: Optional[str] = None, suffix: Optional[str] = None):
        """
        프롬프트 생성을 위한 클래스 초기화
        
        Args:
            prefix (Optional[str]): 프롬프트 앞에 추가할 텍스트
            suffix (Optional[str]): 프롬프트 뒤에 추가할 텍스트
            user_input (Optional[str]): 사용자 입력
        """
        
        self.user_input = user_input
        self.prefix = prefix or "다음 내용을 바탕으로 텍스트를 생성해주세요:"
        self.suffix = suffix or "생성된 텍스트:"

    def generate_prompt(self, request_data: Dict[str, Any]) -> str:
        """
        주어진 요청 데이터를 기반으로 프롬프트를 생성합니다.
        
        Args:
            request_data (Dict[str, Any]): 요청 데이터
            
        Returns:
            str: 생성된 프롬프트
        """
        
        output_parser = StrOutputParser()
        
        # 요청 데이터에서 필요한 정보 추출
        prompt = request_data.get('prompt', '')
        description = request_data.get('description', '')
        current_program = request_data.get('current_program', {})
        target_program = request_data.get('target_program', {})
        
        # 프롬프트 템플릿 생성
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.prefix),
            ("user", f"요청: {prompt}\n설명: {description}\n현재 프로그램: {current_program.get('type', '')} - {current_program.get('context', '')}\n대상 프로그램: {target_program.get('type', '')} - {target_program.get('context', '')}"),
            ("user", self.suffix)
        ])
        
        llm = ChatOpenAI(model="gpt-4",
                         api_key=api_key,
                         temperature=0.5
                         )
        
        chain = prompt_template | llm | output_parser
        
        response = chain.invoke({})
        
        return response
        