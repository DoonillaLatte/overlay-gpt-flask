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

@register_prompt("freestyle")
class FreestylePrompt():
    def __init__(self, user_input: Optional[str] = None, prefix: Optional[str] = None):
        """
        프롬프트 생성을 위한 클래스 초기화
        
        Args:
            prefix (Optional[str]): 프롬프트 앞에 추가할 텍스트
            user_input (Optional[str]): 사용자 입력
        """
        
        self.user_input = user_input
        self.prefix = prefix or """
        주어진 파일의 형식의 마크업 코드를 분석하여, 프롬프트 요구를 충족하도록 마크업 코드를 작성 후 출력해주세요. 
        내용 추가, 내용 수정, 내용 삭제 등 프롬프트 요구에 맞추어 내용을 작성해주세요.
        출력되는 내용은 반드시 명시된 마크업 방식이어야 합니다.
        제목은 생략하고 내용만 출력해주세요.
        """
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
            examples = request_data.get('examples', [])
            
            # MemoryManager를 통해 메모리 가져오기
            memory = MemoryManager.get_memory()
            
            # 파일 타입에 따른 마크업 문법 설정
            file_type = current_program.get('fileType', '').lower() if current_program else ''
            markup_type = "html"  # 기본값
            markup_instruction = ""
            
            if file_type in ['word', 'excel']:
                markup_type = "html"
                markup_instruction = """
                HTML 마크업 규칙:
                1. 모든 태그는 올바르게 열리고 닫혀야 합니다.
                2. Word/Excel 문서의 경우 <table>, <tr>, <td> 태그를 사용하여 표를 구성합니다.
                3. 텍스트 서식은 <p>, <span>, <div> 등의 태그를 사용합니다.
                4. 스타일은 style 속성을 통해 지정합니다.
                """
            elif file_type == 'hwp':
                markup_type = "xml"
                markup_instruction = """
                HWP XML 마크업 규칙:
                1. <HWPML> 루트 태그로 시작합니다.
                2. <SECTION> 태그로 문서 섹션을 구분합니다.
                3. <PARA> 태그로 문단을 구분합니다.
                4. <TEXT> 태그로 텍스트 내용을 포함합니다.
                5. 모든 태그는 올바른 네임스페이스를 사용해야 합니다.
                """
            elif file_type == 'ppt':
                markup_type = "html"
                markup_instruction = """
                PPT HTML 마크업 규칙:
                
                ### 기본 텍스트 스타일
                ```css
                - 글꼴 크기: font-size: [size]pt
                - 글꼴 이름: font-family: [fontName]
                - 글자 굵기: font-weight: Bold/Normal
                - 이탤릭: font-style: italic
                - 밑줄: text-decoration: underline
                - 취소선: <s>태그
                - 텍스트 색상: color: #[rgbColor]
                ```

                ### 배경 스타일
                ```css
                - 배경색: background-color: rgba(r, g, b, alpha)
                - 하이라이트: background-color: rgb(r, g, b)
                ```

                ## 2. 정렬 스타일

                ### 수평 정렬
                ```css
                - center: justify-content: center
                - right: justify-content: flex-end
                - left: justify-content: flex-start
                ```

                ### 수직 정렬
                ```css
                - middle: align-items: center
                - bottom: align-items: flex-end
                - top: align-items: flex-start
                ```

                ## 3. 도형 스타일

                ### 기본 도형 속성
                ```css
                - 위치: position: absolute
                - 좌표: left: [x]px, top: [y]px
                - 크기: width: [width]px, height: [height]px
                - 회전: transform: rotate([angle]deg)
                ```

                ### 테두리와 효과
                ```css
                - 테두리: border: [weight]px [style] [color]
                - 그림자: box-shadow: [x]px [y]px [blur]px rgba(r,g,b,alpha)
                - 모서리 둥글기: border-radius: [radius]px
                - Z-인덱스: z-index: [position]
                ```

                ## 4. HTML 태그 변환

                ### 도형 타입별 태그
                ```html
                - 자동 도형: <div>
                - 불릿포인트: <br><br>
                - 그림: <img src='[절대경로]/images/[GUID].png' alt='Image' />
                - 텍스트 상자: <div>
                - 선: <div>
                - 차트: <div>
                - 표: <table>
                - SmartArt: <div>
                ```

                ### 이미지 처리
                ```css
                - 저장 형식: PNG
                - 저장 위치: [프로그램경로]/images/
                - 파일명: [GUID].png
                - 참조 방식: 절대 경로 사용
                ```

                ## 5. 특수 효과

                ### 3D 효과
                ```css
                - transform-style: preserve-3d
                - perspective: 1000px
                - transform: rotateX() rotateY()
                ```

                ### 그라데이션
                ```css
                - background: linear-gradient(direction, color-stops)
                ```

                ## 6. 변환 처리 메서드

                주요 변환 메서드:
                - `ConvertShapeToHtml()`: 도형을 HTML로 변환
                - `GetStyledText()`: 텍스트 스타일 적용
                - `GetTextStyleString()`: 텍스트 스타일 문자열 생성
                - `GetShapeStyleString()`: 도형 스타일 문자열 생성 


                ## 7. 슬라이드 HTML 변환 구조

                ### 단일 슬라이드 HTML 구조(주의: <div class='Slide1'></div> 같이 전체를 감싸는 div가 없음!!)
                ```html
                <!-- 텍스트 상자 -->
                <div style='position: absolute; left: 100px; top: 50px; width: 200px; height: 100px; color: #000000; text-align: center;'>
                    <span style='font-size: 24pt; font-weight: bold;'>제목</span>
                </div>

                <!-- 이미지 -->
                <div style='position: absolute; left: 150px; top: 150px; width: 300px; height: 200px;'>
                    <img src='[절대경로]/images/[GUID].png' alt='Image' />
                </div>

                <!-- 도형 -->
                <div style='position: absolute; left: 200px; top: 250px; width: 150px; height: 150px; background-color: rgba(255, 255, 255, 0.8); border-radius: 10px;'>
                    <span style='font-size: 16pt;'>내용</span>
                </div>
                ```

                ### 전체 슬라이드 HTML 구조(이 때는 각 슬라이드 페이지를 감싸는 div가 있음)
                ```html
                <div class='Slide1'>
                    <!-- 슬라이드 1의 내용 -->
                </div>
                <div class='Slide2'>
                    <!-- 슬라이드 2의 내용 -->
                </div>
                <!-- 추가 슬라이드들... -->
                ```

                ### 슬라이드 요소 변환 예시
                ```html
                <div class='Slide1'>
                    <!-- 텍스트 상자 -->
                    <div style='position: absolute; left: 100px; top: 50px; width: 200px; height: 100px; color: #000000; text-align: center;'>
                        <span style='font-size: 24pt; font-weight: bold;'>제목</span>
                    </div>
                    
                    <!-- 이미지 (절대 경로 사용) -->
                    <div style='position: absolute; left: 150px; top: 150px; width: 200px; height: 200px;'>
                        <img src='[절대경로]/images/[GUID].png' alt='Image' style='width: 100%; height: 100%; object-fit: contain;' />
                    </div>
                    
                    <!-- 도형 -->
                    <div style='position: absolute; left: 200px; top: 250px; width: 150px; height: 150px; background-color: rgba(255, 255, 255, 0.8); border-radius: 10px;'>
                        <span style='font-size: 16pt;'>내용</span>
                    </div>
                </div>
                ```
                
                ### 불릿포인트 처리
                ```html
                <br><br>
                ```

                ### 저장 위치
                - 변환된 HTML은 `test.html` 파일로 저장됩니다.
                - 각 슬라이드의 모든 요소와 스타일이 보존됩니다.
                - 슬라이드 번호는 `Slide1`, `Slide2` 등의 클래스로 구분됩니다.
                """
            
            # 프롬프트 템플릿 생성
            if current_program:
                # 예시가 있는 경우
                if examples:
                    examples_text = "\n\n".join([f"예시 {i+1}:\n{example}" for i, example in enumerate(examples)])
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", """input의 요구에 맞추어 답변을 생성하세요."""),
                        ("system", self.prefix),
                        ("system", f"""코드 변환 전용 AI입니다. 주석이나 설명 없이 {markup_type} 마크업 코드만을 출력해주세요."""),
                        ("system", markup_instruction),
                        ("system", f"""다음은 {current_program.get('fileType', '')} 파일 문법과 형식의 예시입니다. 
                            이 예시들의 {markup_type} 마크업 문법만을 참고하여 요청을 문법에 맞추어 응답해주세요:
                            
                            {examples_text}"""),
                        ("human", "{input}"),
                        ("ai", "{chat_history}"),
                        ("human", f"""사용자 요청: {prompt}
                            
                            주어진 파일 정보:
                            - 파일명: {current_program.get('fileName', '')}
                            - 파일 형식: {current_program.get('fileType', '')}
                            - 파일 내용:
                            {current_program.get('context', '')}
                            """)
                    ])
                else:
                    prompt_template = ChatPromptTemplate.from_messages([
                        ("system", """input의 요구에 맞추어 답변을 생성하세요."""),
                        ("system", self.prefix),
                        ("system", f"""코드 변환 전용 AI입니다. 주석이나 설명 없이 {markup_type} 마크업 코드만을 출력해주세요."""),
                        ("system", markup_instruction),
                        ("human", "{input}"),
                        ("ai", "{chat_history}"),
                        ("human", f"""사용자 요청: {prompt}
                            
                            주어진 파일 정보:
                            - 파일명: {current_program.get('fileName', '')}
                            - 파일 형식: {current_program.get('fileType', '')}
                            - 파일 내용:
                            {current_program.get('context', '')}
                            """)
                    ])
            else:
                prompt_template = ChatPromptTemplate.from_messages([
                    ("system", """input의 요구에 맞추어 답변을 생성하세요."""),
                    ("system", self.prefix),
                    ("system", """코드 생성 전용 AI입니다. 주석이나 설명 없이 코드만을 출력해주세요."""),
                    ("human", "{input}"),
                    ("ai", "{chat_history}"),
                    ("human", f"사용자 요청: {prompt}")
                ])
            
            llm = ChatOpenAI(model="gpt-4.1",
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