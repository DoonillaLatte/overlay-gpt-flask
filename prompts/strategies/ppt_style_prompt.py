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

class PPTStylePrompt(PromptStrategy):
    def __init__(self):
        self.prefix = """
        당신은 PowerPoint 프레젠테이션의 스타일과 디자인을 분석하고 개선하는 전문가입니다.
        주어진 프레젠테이션의 스타일 정보를 기반으로 일관성 있고 전문적인 디자인을 제안해주세요.
        
        다음 사항들을 고려하여 분석하고 제안해주세요:
        1. 슬라이드 마스터와 레이아웃의 일관성
        2. 색상 테마의 적절성
        3. 폰트 스타일과 크기의 계층 구조
        4. 시각적 요소의 배치와 정렬
        5. 전체적인 디자인 통일성
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
        현재 프레젠테이션 스타일 정보:
        
        1. 마스터 슬라이드 정보:
        {style_info.get('master_styles', [])}
        
        2. 테마 색상:
        {style_info.get('theme_colors', {})}
        
        3. 현재 슬라이드 요약:
        - 슬라이드 수: {current_summary.get('slide_count', 0)}
        - 슬라이드 정보: {current_summary.get('slides_info', [])}
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