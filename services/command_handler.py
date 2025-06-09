import os
import html
import logging
import base64
import re
from typing import Dict, Any
from .vector_db_service import VectorDBService
from databases.vector_database import VectorDatabase
from prompts.prompt_factory import PromptFactory

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
                'get_workflows': self._handle_request_top_workflows
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
            
            # 파일 형식에 따른 예시 검색
            examples = []
            current_program = content.get('current_program') or {}
            if current_program:
                file_type = current_program.get('fileType')
                if file_type:
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
            
            # 제목 생성
            title = None
            file_type = 'word'  # 기본값으로 word 사용
            if current_program and current_program.get('fileType'):
                file_type = current_program['fileType']
                
            vector_db = self.vector_db_service._get_db_by_type(file_type)
            title = vector_db._generate_title(content['prompt'])
            
            return {
                'command': f'generated_response',
                'chat_id': message.get('chat_id'),
                'title': title,
                'message': response,
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