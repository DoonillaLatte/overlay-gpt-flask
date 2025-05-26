from typing import Optional, Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from registry import register_prompt
import logging

logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")

@register_prompt("convert_prompt")
class ConvertPrompt():
    def __init__(self, user_input: Optional[str] = None, prefix: Optional[str] = None, suffix: Optional[str] = None):
        """
        프롬프트 생성을 위한 클래스 초기화
        
        Args:
            prefix (Optional[str]): 프롬프트 앞에 추가할 텍스트
            suffix (Optional[str]): 프롬프트 뒤에 추가할 텍스트
            user_input (Optional[str]): 사용자 입력
        """
        
        self.user_input = user_input
        self.prefix = prefix or "주어진 파일의 형식의 html코드를 분석하여 요청에 따라 대상 프로그램의 형식에 맞는 html코드를 작성해주세요."
        self.suffix = suffix or "답변:"

    def generate_prompt(self, request_data: Dict[str, Any]) -> str:
        """
        주어진 요청 데이터를 기반으로 프롬프트를 생성합니다.
        
        Args:
            request_data (Dict[str, Any]): 요청 데이터
                - prompt (str): 변환 요청 내용
                - description (str): 변환에 대한 설명
                - current_program (dict): 현재 프로그램 정보
                - target_program (dict): 대상 프로그램 정보
                - file_id (str): 변환할 파일 ID
            
        Returns:
            str: 생성된 프롬프트
            
        Raises:
            ValueError: 필수 입력값이 누락된 경우
        """
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
        current_program = request_data.get('current_program')
        target_program = request_data.get('target_program')
        
        # 프롬프트 템플릿 생성
        if current_program:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prefix),
                ("user", f"""사용자 요청: {prompt}
                    첨부된 파일 정보:
                    - 파일명: {current_program.get('fileName', '')}
                    - 파일 형식: {current_program.get('fileType', '')}
                    - 파일 내용:
                    {current_program.get('context', '')}"""),
                ("user", self.suffix)
            ])
        else:
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prefix),
                ("user", f"사용자 요청: {prompt}"),
                ("user", self.suffix)
            ])
        
        llm = ChatOpenAI(model="gpt-4",
                         api_key=api_key,
                         temperature=0.7
                         )
        
        chain = prompt_template | llm | output_parser
        
        response = chain.invoke({})
        
        return response
