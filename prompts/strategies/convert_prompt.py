from typing import Optional, Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from registry import register_prompt
api_key = os.getenv("OPENAI_API_KEY")

@register_prompt("convert")
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
        self.prefix = prefix or "다음 내용을 변환해주세요:"
        self.suffix = suffix or "변환된 내용:"

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
        try:
            # 필수 입력값 검증
            required_fields = ['prompt', 'current_program', 'target_program', 'file_id']
            for field in required_fields:
                if field not in request_data:
                    raise ValueError(f"필수 입력값 '{field}'가 누락되었습니다.")
            
            output_parser = StrOutputParser()
            
            # 요청 데이터에서 필요한 정보 추출
            prompt = request_data['prompt']
            description = request_data.get('description', '')
            current_program = request_data['current_program']
            target_program = request_data['target_program']
            file_id = request_data['file_id']
            
            # 프롬프트 템플릿 생성
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", self.prefix),
                ("user", f"요청: {prompt}\n설명: {description}\n현재 프로그램: {current_program.get('type', '')} - {current_program.get('context', '')}\n대상 프로그램: {target_program.get('type', '')} - {target_program.get('context', '')}\n파일 ID: {file_id}"),
                ("user", self.suffix)
            ])
            
            llm = ChatOpenAI(model="gpt-4",
                            api_key=api_key,
                            temperature=0.1
                            )
            
            chain = prompt_template | llm | output_parser
            
            response = chain.invoke({})
            
            return response
            
        except Exception as e:
            raise Exception(f"프롬프트 생성 중 오류가 발생했습니다: {str(e)}")
