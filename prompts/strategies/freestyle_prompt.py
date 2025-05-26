from typing import Optional, Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from registry import register_prompt
import logging

logger = logging.getLogger(__name__)

api_key = os.getenv("OPENAI_API_KEY")

@register_prompt("freestyle")
class FreestylePrompt():
    def __init__(self, user_input: Optional[str] = None, prefix: Optional[str] = None, suffix: Optional[str] = None):
        """
        프롬프트 생성을 위한 클래스 초기화
        
        Args:
            prefix (Optional[str]): 프롬프트 앞에 추가할 텍스트
            suffix (Optional[str]): 프롬프트 뒤에 추가할 텍스트
            user_input (Optional[str]): 사용자 입력
        """
        
        self.user_input = user_input
        self.prefix = prefix or "다음 내용을 자유롭게 작성해주세요:"
        self.suffix = suffix or "작성된 내용:"

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
        current_program = request_data.get('current_program')
        examples = request_data.get('examples', [])
        
        # 프롬프트 템플릿 생성
        if current_program:
            # 예시가 있는 경우
            if examples:
                examples_text = "\n\n".join([f"예시 {i+1}:\n{example}" for i, example in enumerate(examples)])
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", self.prefix),
                    ("system", f"""다음은 {current_program.get('fileType', '')} 파일 형식의 예시입니다. 
                        이 예시들을 참고하여 요청에 응답해주세요:
                        
                        {examples_text}"""),
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
                ("system", """파일 내용은 HTML 마크업 형식으로 제공됩니다. 
                    마크업을 해석하여 내용을 이해하고 적절히 응답해주세요."""),
                ("user", f"""사용자 요청: {prompt}
                    첨부된 파일 정보:
                    - 파일명: {current_program.get('fileName', '')}
                    - 파일 형식: {current_program.get('fileType', '')}
                    - 파일 내용 (HTML 마크업):
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
        