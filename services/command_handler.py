import os
import html
import logging
import base64
import re
from typing import Dict, Any
from .vector_db_service import VectorDBService
from databases.vector_database import VectorDatabase
from prompts.prompt_factory import PromptFactory
import codecs
import unicodedata

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, vector_db_service: VectorDBService, prompt_factory: PromptFactory):
        self.vector_db_service = vector_db_service
        self.prompt_factory = prompt_factory

    def handle_command(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        메시지의 command에 따라 적절한 처리를 수행합니다.
        
        Args:
            message (Dict[str, Any]): 처리할 메시지
            
        Returns:
            Dict[str, Any]: 응답 메시지
        """
        try:
            command = message.get('command')
            
            # 명령어별 처리 함수 매핑
            command_handlers = {
                'request_prompt': self._handle_response,
                'get_workflows': self._handle_request_top_workflows,
                'apply_response': self._handle_apply_response
            }
            
            # 매핑된 핸들러 실행
            handler = command_handlers.get(command)
            if handler:
                return handler(message)
            else:
                return {
                    'command': f'generated_response',
                    'chat_id': message.get('chat_id'),
                    'message': f'지원하지 않는 명령어입니다: {command}',
                    'status': 'error'
                }
                
        except Exception as e:
            logger.error(f"명령어 처리 중 오류 발생: {str(e)}", exc_info=True)
            return {
                'command': f'generated_response',
                'chat_id': message.get('chat_id'),
                'message': str(e),
                'status': 'error'
            }

    def _handle_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """응답 생성 처리"""
        try:
            content = {
                'chat_id': message.get('chat_id'),
                'prompt': message.get('prompt'),
                'request_type': message.get('request_type'),
                'current_program': message.get('current_program'),
                'target_program': message.get('target_program')
            }
            
            logger.info(f"요청 내용: {content}")
            
            # 필수 필드 검증
            if not content['prompt']:
                raise ValueError("prompt는 필수 입력값입니다.")
            if not content['request_type']:
                raise ValueError("request_type은 필수 입력값입니다.")
            
            current_program = content.get('current_program') or {}
            
            if current_program and current_program.get('fileType') == 'text':
                strategy_name = "convert_for_text"
            else:
                # target_program이 있는 경우 convert_prompt 사용
                if content.get('target_program'):
                    strategy_name = "convert"
                else:
                    strategy_name = {
                        1: "freestyle",         #마크업 코드로 자유 작성
                        2: "generate_text",     #파일의 내용 추가
                        3: "modify_text",       #파일의 내용 수정
                        4: "check_spelling",    #파일의 내용 맞춤법 검사
                        5: "convert",           #주어진 파일을 근거로 대상 파일의 내용 변환
                        6: "freestyle_text"     #마크업 코드가 아닌 텍스트 형식의 리턴
                    }.get(content['request_type'], "freestyle")
            
            logger.info(f"선택된 전략: {strategy_name}")
            
            strategy = self.prompt_factory.get_strategy(strategy_name)
            
            # current_program이 있을 경우 vector DB에 저장
            if current_program and current_program.get('fileId') and current_program.get('context'):
                try:
                    self.vector_db_service.store_program_info(
                        file_id=current_program.get('fileId'),
                        file_type=current_program.get('fileType'),
                        context=current_program.get('context'),
                        volume_id=current_program.get('volumeId')
                    )
                    logger.info(f"현재 프로그램 정보를 vector DB에 저장했습니다 - FileID: {current_program.get('fileId')}, FileType: {current_program.get('fileType')}")
                except Exception as e:
                    logger.warning(f"Vector DB 저장 실패 (계속 진행): {str(e)}")
            
            #target_program이 있는 경우 vector DB에 저장
            if content.get('target_program'):
                try:
                    self.vector_db_service.store_program_info(
                        file_id=content.get('target_program').get('fileId'),
                        file_type=content.get('target_program').get('fileType'),
                        context=content.get('target_program').get('context'),
                        volume_id=content.get('target_program').get('volumeId')
                    )
                    logger.info(f"대상 프로그램 정보를 vector DB에 저장했습니다 - FileID: {content.get('target_program').get('fileId')}, FileType: {content.get('target_program').get('fileType')}")
                except Exception as e:
                    logger.warning(f"Vector DB 저장 실패 (계속 진행): {str(e)}")
            
            # 파일 형식에 따른 예시 검색
            examples = []
            if current_program:
                file_type = current_program.get('fileType')
                # text 타입은 예시 검색하지 않음
                if file_type and file_type != 'text':
                    # 파일 형식에 맞는 예시 검색
                    similar_examples = self.vector_db_service.search_similar_programs(
                        query=f"fileType:{file_type}",
                        file_type=file_type,
                        k=3
                    )
                    examples = [example.get('context', '') for example in similar_examples]
            
            # 예시를 content에 추가
            content['examples'] = examples
            
            logger.info(f"전략 실행 전 content: {content}")
            response = strategy.generate_prompt(content)
            logger.info(f"전략 실행 결과: {response}")
            
            # HTML 엔티티 디코딩
            response = html.unescape(response)
            logger.info(f"HTML 디코딩 후: {response}")
            
            # 유니코드 이스케이프 시퀀스 디코딩 (백슬래시 문제 해결)
            try:
                # 백슬래시가 포함된 경로에서 \b, \n 등이 잘못 해석되지 않도록 처리
                # 먼저 이미지 경로를 Base64로 변환 (원본 경로가 손상되기 전에)
                response = self._convert_images_to_base64(response)
                logger.info(f"이미지 Base64 변환 후 응답 길이: {len(response)}")
                
                # 이제 유니코드 디코딩 (이미지 경로는 이미 Base64로 변환됨)
                response = response.encode('utf-8').decode('unicode_escape').encode('latin1').decode('utf-8')
                logger.info(f"유니코드 디코딩 후: {response}")
            except (UnicodeDecodeError, UnicodeEncodeError) as e:
                logger.warning(f"유니코드 디코딩 실패, Base64 변환만 적용: {str(e)}")
                # 유니코드 디코딩이 실패해도 Base64 변환은 이미 완료됨
            
            # 원본 응답을 적용용으로 보관 (dotnet에서 사용)
            apply_message = response
            
            # HTML 정규화 (Vue 표시용)
            display_message = self._normalize_html_for_document(response, content.get('current_program', {}).get('fileType', 'unknown'))
            logger.info(f"HTML 정규화 후 표시용 응답 길이: {len(display_message)}")
            
            # 제목 생성
            title = None
            title_file_type = 'word'  # 기본값으로 word 사용
            if current_program and current_program.get('fileType'):
                current_file_type = current_program['fileType']
                # text 타입이면 target_program의 fileType 사용, 없으면 word
                if current_file_type == 'text':
                    target_program = content.get('target_program', {})
                    title_file_type = target_program.get('fileType', 'word')
                else:
                    title_file_type = current_file_type
                
            vector_db = self.vector_db_service._get_db_by_type(title_file_type)
            title = vector_db._generate_title(content['prompt'])
            
            return {
                'command': f'generated_response',
                'chat_id': message.get('chat_id'),
                'title': title,
                'vue_content': display_message,       # Vue 표시용 (정규화된 HTML)
                'dotnet_content': apply_message,      # dotnet 적용용 (원본 HTML)
                'status': 'success'
            }
        except ValueError as e:
            logger.error(f"잘못된 요청: {str(e)}")
            return {
                'command': 'generated_response',
                'chat_id': message.get('chat_id'),
                'message': str(e),
                'status': 'error'
            }
        except Exception as e:
            logger.error(f"응답 생성 중 오류 발생: {str(e)}", exc_info=True)
            return {
                'command': 'generated_response',
                'chat_id': message.get('chat_id'),
                'message': f'처리 중 오류가 발생했습니다: {str(e)}',
                'status': 'error'
            }

    def _handle_request_top_workflows(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """유사 컨텍스트 검색 처리"""
        try:
            content = {
                'chat_id': message.get('chat_id'),
                'file_type': message.get('file_type'),
                'current_program': message.get('current_program')
            }
            
            multi_file_id = content['current_program']['fileId']
            multi_file_type = content['current_program']['fileType']
            multi_file_context = content['current_program']['context']
            multi_volume_id = content['current_program']['volumeId']
            request_file_type = content['file_type']
            
            # text 타입 처리
            if multi_file_type == 'text':
                logger.info(f"텍스트 타입 워크플로우 검색 - 요청 파일 타입: {request_file_type}")
                
                # text는 DB에 저장하지 않음
                # 텍스트 내용으로 요청 파일 타입 DB에서 유사한 프로그램 검색
                similar_programs = self.vector_db_service.search_similar_programs(
                    query=multi_file_context[:500],  # 텍스트 앞부분을 쿼리로 사용
                    file_type=request_file_type,
                    k=5
                )
                
                # 유사한 프로그램의 ID 리스트 추출
                similar_program_ids = [[program['fileId'], program['volumeId']] for program in similar_programs]
                
                logger.info(f"텍스트 기반 유사 문서 {len(similar_program_ids)}개 발견")
                
            else:
                # 일반 파일 처리
                # 벡터 데이터베이스에 프로그램 정보 저장
                self.vector_db_service.store_program_info(
                    file_id=multi_file_id,
                    file_type=multi_file_type,
                    context=multi_file_context,
                    volume_id=multi_volume_id
                )
                
                # 유사한 프로그램 검색
                similar_programs = self.vector_db_service.search_similar_programs(
                    query=multi_file_context,
                    file_type=request_file_type,
                    k=5
                )
                
                # 유사한 프로그램의 ID 리스트 추출
                similar_program_ids = [[program['fileId'], program['volumeId']] for program in similar_programs]
            
            return {
                'command': 'response_workflows',
                'chat_id': content['chat_id'],
                'similar_program_ids': similar_program_ids,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"유사 컨텍스트 검색 중 오류 발생: {str(e)}")
            return {
                'command': 'response_workflows',
                'chat_id': content['chat_id'],
                'message': f'유사한 프로그램 검색 중 오류 발생: {str(e)}',
                'status': 'error'
            }

    def _handle_apply_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """응답 적용 처리 - 원본 HTML을 dotnet으로 전송"""
        try:
            chat_id = message.get('chat_id')
            apply_content = message.get('apply_content')  # Vue에서 전송한 원본 HTML
            
            logger.info(f"응답 적용 요청 - Chat ID: {chat_id}")
            logger.info(f"적용할 콘텐츠 길이: {len(apply_content) if apply_content else 0}")
            
            if not apply_content:
                return {
                    'command': 'apply_response_result',
                    'chat_id': chat_id,
                    'message': '적용할 콘텐츠가 없습니다.',
                    'status': 'error'
                }
            
            # dotnet으로 원본 HTML 전송 로직
            # 여기에 dotnet 통신 코드를 추가할 수 있습니다.
            logger.info("dotnet으로 원본 HTML 전송...")
            
            return {
                'command': 'apply_response_result',
                'chat_id': chat_id,
                'message': '응답이 성공적으로 적용되었습니다.',
                'apply_content': apply_content,  # dotnet이 받을 원본 HTML
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"응답 적용 중 오류 발생: {str(e)}", exc_info=True)
            return {
                'command': 'apply_response_result',
                'chat_id': message.get('chat_id'),
                'message': f'응답 적용 중 오류 발생: {str(e)}',
                'status': 'error'
            }

    def _convert_images_to_base64(self, html_content: str) -> str:
        """HTML 콘텐츠에서 이미지 파일 경로를 Base64 데이터 URL로 변환"""
        try:
            # img 태그의 src 속성에서 로컬 파일 경로를 찾아 Base64로 변환
            def replace_img_src(match):
                try:
                    # src 속성에서 파일 경로 추출
                    src_attr = match.group(1)
                    
                    # 파일 경로 정리 (따옴표 제거)
                    file_path = src_attr.replace("'", "").replace('"', '').strip()
                    
                    logger.info(f"이미지 파일 경로: {file_path}")
                    
                    # 파일이 존재하는지 확인
                    if os.path.exists(file_path):
                        # 파일 확장자에 따른 MIME 타입 결정
                        file_ext = os.path.splitext(file_path)[1].lower()
                        mime_type = {
                            '.png': 'image/png',
                            '.jpg': 'image/jpeg',
                            '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif',
                            '.bmp': 'image/bmp',
                            '.webp': 'image/webp'
                        }.get(file_ext, 'image/png')
                        
                        # 파일을 읽어서 Base64로 인코딩
                        with open(file_path, 'rb') as img_file:
                            img_data = img_file.read()
                            base64_data = base64.b64encode(img_data).decode('utf-8')
                            
                        # Base64 데이터 URL 생성
                        data_url = f"data:{mime_type};base64,{base64_data}"
                        
                        logger.info(f"이미지 Base64 변환 성공: {file_path} -> {len(base64_data)} bytes")
                        
                        # 원래 src 속성을 Base64 데이터 URL로 교체
                        return f"src='{data_url}'"
                    else:
                        logger.warning(f"이미지 파일을 찾을 수 없음: {file_path}")
                        return f"src=''"
                        
                except Exception as e:
                    logger.error(f"이미지 변환 중 오류: {str(e)}")
                    return f"src=''"
            
            # src='...' 패턴을 찾아서 교체
            result = re.sub(r"src='([^']*)'", replace_img_src, html_content)
            result = re.sub(r'src="([^"]*)"', replace_img_src, result)
            
            return result
            
        except Exception as e:
            logger.error(f"이미지 Base64 변환 중 오류: {str(e)}")
            return html_content

    def _normalize_html_for_document(self, html_content: str, document_type: str = "unknown") -> str:
        """모든 문서 타입의 HTML을 Vue 컴포넌트와 호환되도록 정규화"""
        if not html_content:
            return html_content
            
        logger.info(f"HTML 정규화 시작 - 문서 타입: {document_type}")
        
        # 1. 기본 레이아웃 정규화 (모든 문서 타입 공통)
        normalized_html = self._normalize_basic_layout(html_content)
        
        # 2. 문서 타입별 특화 정규화
        if document_type.lower() in ['powerpoint', 'ppt']:
            normalized_html = self._normalize_powerpoint_specific(normalized_html)
        elif document_type.lower() in ['word', 'docx', 'doc']:
            normalized_html = self._normalize_word_specific(normalized_html)
        elif document_type.lower() in ['excel', 'xlsx', 'xls']:
            normalized_html = self._normalize_excel_specific(normalized_html)
        elif document_type.lower() in ['hwp', 'hanword']:
            normalized_html = self._normalize_hwp_specific(normalized_html)
        
        # 3. 공통 마무리 처리
        normalized_html = self._apply_common_container(normalized_html, document_type)
        
        logger.info(f"HTML 정규화 완료 - 문서 타입: {document_type}")
        return normalized_html
    
    def _normalize_basic_layout(self, html_content: str) -> str:
        """기본 레이아웃 정규화 (모든 문서 타입 공통)"""
        # absolute positioning을 제거하고 block 요소로 변환
        normalized_html = re.sub(
            r"position:\s*absolute;[^'\"]*",
            "position: relative; display: block; margin-bottom: 12px;",
            html_content
        )
        
        # left, top 값 제거
        normalized_html = re.sub(r"left:\s*\d+px;", "", normalized_html)
        normalized_html = re.sub(r"top:\s*\d+px;", "", normalized_html)
        
        # z-index 제거 (Vue 컴포넌트와 겹침 방지)
        normalized_html = re.sub(r"z-index:\s*\d+;", "", normalized_html)
        
        # width를 반응형으로 조정
        normalized_html = re.sub(
            r"width:\s*\d+px;",
            "width: 100%; max-width: 100%;",
            normalized_html
        )
        
        # height auto로 조정
        normalized_html = re.sub(
            r"height:\s*\d+px;",
            "height: auto; min-height: 20px;",
            normalized_html
        )
        
        return normalized_html
    
    def _normalize_powerpoint_specific(self, html_content: str) -> str:
        """PowerPoint 전용 정규화"""
        # 큰 글꼴 크기를 웹에 맞게 조정
        def convert_ppt_font_size(match):
            size_pt = match.group(1)
            try:
                size_num = int(size_pt)
                if size_num >= 36:
                    return "font-size: 24px; font-weight: bold;"
                elif size_num >= 24:
                    return "font-size: 18px;"
                elif size_num >= 18:
                    return "font-size: 16px;"
                else:
                    return "font-size: 14px;"
            except ValueError:
                return "font-size: 16px;"
        
        html_content = re.sub(r"font-size:\s*(\d+)pt;", convert_ppt_font_size, html_content)
        
        # vertical-align middle을 top으로 변경
        html_content = re.sub(r"vertical-align:\s*middle;", "vertical-align: top;", html_content)
        
        return html_content
    
    def _normalize_word_specific(self, html_content: str) -> str:
        """Word 전용 정규화"""
        # Word 특유의 스타일 정규화
        
        # 페이지 여백 제거
        html_content = re.sub(r"margin:\s*\d+pt \d+pt \d+pt \d+pt;", "margin: 8px 0;", html_content)
        
        # Word 표 스타일 정규화
        html_content = re.sub(
            r"border:\s*solid [^;]+;",
            "border: 1px solid #666; border-collapse: collapse;",
            html_content
        )
        
        # Word 글꼴 크기 조정
        def convert_word_font_size(match):
            size_pt = match.group(1)
            try:
                size_num = int(size_pt)
                if size_num >= 18:
                    return "font-size: 18px; font-weight: bold;"
                elif size_num >= 14:
                    return "font-size: 16px;"
                elif size_num >= 12:
                    return "font-size: 14px;"
                else:
                    return "font-size: 12px;"
            except ValueError:
                return "font-size: 14px;"
        
        html_content = re.sub(r"font-size:\s*(\d+)pt;", convert_word_font_size, html_content)
        
        return html_content
    
    def _normalize_excel_specific(self, html_content: str) -> str:
        """Excel 전용 정규화"""
        # Excel 테이블 구조 개선
        
        # 테이블 셀 스타일 정규화
        html_content = re.sub(
            r"border:\s*\.\d+pt [^;]+;",
            "border: 1px solid #999;",
            html_content
        )
        
        # Excel 셀 패딩 조정
        html_content = re.sub(
            r"padding:\s*\d+pt;",
            "padding: 8px;",
            html_content
        )
        
        # 테이블 너비 반응형으로 조정
        html_content = re.sub(
            r"<table[^>]*>",
            '<table style="width: 100%; border-collapse: collapse; margin: 12px 0;">',
            html_content
        )
        
        # Excel 글꼴 크기는 기본적으로 작으므로 적절히 조정
        def convert_excel_font_size(match):
            size_pt = match.group(1)
            try:
                size_num = int(size_pt)
                if size_num <= 8:
                    return "font-size: 12px;"
                elif size_num <= 10:
                    return "font-size: 13px;"
                elif size_num <= 12:
                    return "font-size: 14px;"
                else:
                    return "font-size: 16px;"
            except ValueError:
                return "font-size: 13px;"
        
        html_content = re.sub(r"font-size:\s*(\d+)pt;", convert_excel_font_size, html_content)
        
        return html_content
    
    def _normalize_hwp_specific(self, html_content: str) -> str:
        """HWP(한글) 전용 정규화"""
        # 한글 문서 특유의 스타일 정규화
        
        # 한글 특유의 여백 조정
        html_content = re.sub(r"margin:\s*\d+mm [^;]+;", "margin: 10px 0;", html_content)
        
        # 한글 글꼴 크기 조정 (pt 단위)
        def convert_hwp_font_size(match):
            size_pt = match.group(1)
            try:
                size_num = int(size_pt)
                if size_num >= 16:
                    return "font-size: 18px; font-weight: bold;"
                elif size_num >= 12:
                    return "font-size: 16px;"
                elif size_num >= 10:
                    return "font-size: 14px;"
                else:
                    return "font-size: 12px;"
            except ValueError:
                return "font-size: 14px;"
        
        html_content = re.sub(r"font-size:\s*(\d+)pt;", convert_hwp_font_size, html_content)
        
        # 한글 문서의 줄간격 조정
        html_content = re.sub(r"line-height:\s*\d+\.\d+;", "line-height: 1.6;", html_content)
        
        return html_content
    
    def _apply_common_container(self, html_content: str, document_type: str) -> str:
        """공통 컨테이너 적용"""
        # border-radius 값 조정
        def adjust_border_radius(match):
            radius = match.group(1)
            try:
                radius_num = float(radius)
                if radius_num > 16:
                    return "border-radius: 8px;"
                else:
                    return f"border-radius: {radius}px;"
            except ValueError:
                return "border-radius: 4px;"
        
        html_content = re.sub(r"border-radius:\s*(\d+\.?\d*)px;", adjust_border_radius, html_content)
        
        # 문서 타입별 컨테이너 클래스 적용
        container_class = f"document-content-container {document_type.lower()}-content"
        html_content = f'<div class="{container_class}">{html_content}</div>'
        
        return html_content