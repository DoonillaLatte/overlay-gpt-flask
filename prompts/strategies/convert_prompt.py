from typing import Optional, Dict, Any
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
import os
from registry import register_prompt
import logging
from .memory_manager import MemoryManager

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
        self.prefix = prefix or "주어진 파일의 형식의 html코드를 분석하여 요청에 따라, 대상 프로그램의 형식에 맞는 html코드를 작성 혹은 수정 후 출력해주세요."
        self.suffix = suffix or "답변:"
        self.logger = logging.getLogger(__name__)

    def generate_prompt(self, request_data: Dict[str, Any]) -> str:
        """
        주어진 요청 데이터를 기반으로 프롬프트를 생성합니다.
        
        Args:
            request_data (Dict[str, Any]): 요청 데이터
            
        Returns:
            str: 생성된 프롬프트
        """
        try:
            output_parser = StrOutputParser()
            
            # 요청 데이터에서 필요한 정보 추출
            prompt = request_data.get('prompt', '')
            current_program = request_data.get('current_program')
            target_program = request_data.get('target_program')
            examples = request_data.get('examples', [])
            
            # MemoryManager를 통해 메모리 가져오기
            memory = MemoryManager.get_memory()
            
            # 프롬프트 템플릿 생성
            if current_program:
                # 예시가 있는 경우
                if examples:
                    examples_text = "\n\n".join([f"예시 {i+1}:\n{example}" for i, example in enumerate(examples)])
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", self.prefix),
                        ("system", """코드 변환 전용 AI입니다. 
                            소스 코드의 맥락을 분석하고 사용자의 요청에 따라 새로운 맥락을 생성하거나 수정해주세요.
                            코드만 출력해주세요."""),
                        ("system", f"""다음은 {current_program.get('fileType', '')} 파일 형식의 예시입니다. 
                            이 예시들을 참고하여 요청에 응답해주세요:
                            
                            {examples_text}"""),
                        ("human", "{input}"),
                        ("ai", "{chat_history}"),
                        ("human", f"""사용자 요청: {prompt}
                            
                            소스 파일 정보:
                            - 파일명: {current_program.get('fileName', '')}
                            - 파일 형식: {current_program.get('fileType', '')}
                            - 파일 내용:
                            {current_program.get('context', '')}
                            
                            대상 프로그램 정보:
                            - 파일명: {target_program.get('fileName', '')}
                            - 파일 형식: {target_program.get('fileType', '')}
                            - 파일 내용:
                            {target_program.get('context', '')}"""),
                        ("human", self.suffix)
                    ])
                else:
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", self.prefix),
                        ("system", """코드 변환 전용 AI입니다. 
                            소스 코드의 맥락을 분석하고 사용자의 요청에 따라 새로운 맥락을 생성하거나 수정해주세요.
                            코드만 출력해주세요."""),
                        ("human", "{input}"),
                        ("ai", "{chat_history}"),
                        ("human", f"""사용자 요청: {prompt}
                            
                            소스 파일 정보:
                            - 파일명: {current_program.get('fileName', '')}
                            - 파일 형식: {current_program.get('fileType', '')}
                            - 파일 내용:
                            {current_program.get('context', '')}
                            
                            대상 프로그램 정보:
                            - 파일명: {target_program.get('fileName', '')}
                            - 파일 형식: {target_program.get('fileType', '')}
                            - 파일 내용:
                            {target_program.get('context', '')}"""),
                        ("human", self.suffix)
                    ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", self.prefix),
                    ("system", """코드 생성 전용 AI입니다. 
                        사용자의 요청에 따라 새로운 코드를 생성하거나 수정해주세요.
                        코드만 출력해주세요."""),
                    ("human", "{input}"),
                    ("ai", "{chat_history}"),
                    ("human", f"사용자 요청: {prompt}"),
                    ("human", self.suffix)
                ])
            
            llm = ChatOpenAI(model="gpt-4.1-nano",
                            api_key=api_key,
                            temperature=0.5
                            )
            
            chain = LLMChain(
                llm=llm,
                prompt=prompt_template,
                memory=memory,
                verbose=True
            )
            
            response = chain.predict(input=prompt)
            
            return response
        
        except Exception as e:
            self.logger.error(f"프롬프트 생성 중 오류 발생: {str(e)}", exc_info=True)
            raise
