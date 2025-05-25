from typing import Dict, Any, Optional
from ..prompt_strategy import PromptStrategy
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class WordStylePrompt(PromptStrategy):
    def __init__(self):
        self.prefix = """
        당신은 Word 문서의 스타일과 서식을 분석하고 개선하는 전문가입니다.
        주어진 문서의 스타일 정보를 기반으로 일관성 있고 전문적인 서식을 제안해주세요.
        
        다음 사항들을 고려하여 분석하고 제안해주세요:
        1. 문단 스타일의 일관성
        2. 글꼴 스타일과 크기의 계층 구조
        3. 문자 스타일의 적절성
        4. 표 스타일의 통일성
        5. 전체적인 문서 서식의 전문성
        """
        
        self.suffix = """
        위의 분석을 바탕으로 구체적인 개선 방안을 제시해주세요.
        """

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
        style_info = request_data.get('style_definitions', {})
        current_summary = request_data.get('summary', {})
        
        # 스타일 정보를 문자열로 변환
        style_info_str = f"""
        현재 Word 문서 스타일 정보:
        
        1. 문단 스타일:
        {style_info.get('paragraph_styles', {})}
        
        2. 문자 스타일:
        {style_info.get('character_styles', {})}
        
        3. 표 스타일:
        {style_info.get('table_styles', {})}
        
        4. 현재 문서 요약:
        - 단락 수: {current_summary.get('paragraphs_count', 0)}
        - 표 수: {current_summary.get('tables_count', 0)}
        - 단락 정보: {current_summary.get('paragraphs_info', [])}
        - 표 정보: {current_summary.get('tables_info', [])}
        """
        
        # 프롬프트 템플릿 생성
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.prefix),
            ("user", style_info_str),
            ("user", self.suffix)
        ])
        
        llm = ChatOpenAI(model="gpt-4",
                         api_key=api_key,
                         temperature=0.7
                         )
        
        chain = prompt_template | llm | output_parser
        
        response = chain.invoke({})
        
        return response 