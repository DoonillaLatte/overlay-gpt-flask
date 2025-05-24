from typing import Dict, Any
import logging
from .vector_db_service import VectorDBService
from .excel_service import ExcelService
from prompts.prompt_factory import PromptFactory
import base64
from io import BytesIO
import json

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, vector_db_service: VectorDBService, prompt_factory: PromptFactory):
        self.vector_db_service = vector_db_service
        self.prompt_factory = prompt_factory
        self.excel_service = ExcelService()

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
                'request_single_generated_response': self._handle_single_response,
                'search_similar_context': self._handle_similar_context_search,
                'run_convert_prompt': self._handle_convert_prompt
            }
            
            # 파일 데이터가 있는 경우 엑셀 처리
            if 'file_data' in message:
                return self._handle_excel_file(message['file_data'])
            
            # 매핑된 핸들러 실행
            handler = command_handlers.get(command)
            if handler:
                return handler(message)
            else:
                return {
                    'command': 'response_single_generated_response',
                    'message': f'지원하지 않는 명령어입니다: {command}',
                    'status': 'error'
                }
                
        except Exception as e:
            logger.error(f"명령어 처리 중 오류 발생: {str(e)}", exc_info=True)
            return {
                'message': str(e),
                'status': 'error'
            }

    def _handle_single_response(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """단일 응답 생성 처리"""
        try:
            content = {
                'chat_id': message.get('chat_id'),
                'prompt': message.get('prompt'),
                'request_type': message.get('request_type'),
                'description': message.get('description'),
                'current_program': message.get('current_program'),
                'target_program': message.get('target_program')
            }
            
            strategy_name = {
                1: "explain",
                2: "freestyle",
                3: "generate_text",
                4: "summary"
            }.get(content['request_type'], "explain")
            
            strategy = self.prompt_factory.get_strategy(strategy_name)
            response = strategy.generate_prompt(content)
            
            return {
                'command': 'response_single_generated_response',
                'message': response,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"단일 응답 생성 중 오류 발생: {str(e)}")
            return {
                'command': 'response_single_generated_response',
                'message': f'프롬프트 처리 중 오류 발생: {str(e)}',
                'status': 'error'
            }

    def _handle_similar_context_search(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """유사 컨텍스트 검색 처리"""
        try:
            content = {
                'chat_id': message.get('chat_id'),
                'prompt': message.get('prompt'),
                'request_type': message.get('request_type'),
                'description': message.get('description'),
                'current_program': message.get('current_program'),
                'target_program': message.get('target_program')
            }
            
            multi_program_id = content['target_program']['id']
            multi_program_type = content['target_program']['type']
            multi_program_context = content['target_program']['context']
            
            # 벡터 데이터베이스에 프로그램 정보 저장
            self.vector_db_service.store_program_info(
                program_id=multi_program_id,
                program_type=multi_program_type,
                program_context=multi_program_context
            )
            
            # 유사한 프로그램 검색
            similar_programs = self.vector_db_service.search_similar_programs(
                query=multi_program_context,
                k=5
            )
            
            # 유사한 프로그램의 ID 리스트 추출
            similar_program_ids = [program['id'] for program in similar_programs]
            
            return {
                'command': 'search_similar_context',
                'similar_program_ids': similar_program_ids,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"유사 컨텍스트 검색 중 오류 발생: {str(e)}")
            return {
                'command': 'search_similar_context',
                'message': f'유사한 프로그램 검색 중 오류 발생: {str(e)}',
                'status': 'error'
            }

    def _handle_convert_prompt(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """프롬프트 변환 처리"""
        try:
            strategy = self.prompt_factory.get_strategy(message.get('request_type'))
            response = strategy.generate_prompt(message)
            
            return {
                'command': 'response_multiple_generated_response',
                'message': response,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"프롬프트 변환 중 오류 발생: {str(e)}")
            return {
                'command': 'response_multiple_generated_response',
                'message': f'프롬프트 처리 중 오류 발생: {str(e)}',
                'status': 'error'
            }

    def _handle_excel_file(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """엑셀 파일 처리"""
        try:
            if file_data.get('content_type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                logger.info(f"엑셀 파일 처리 시작: {file_data.get('filename')}")
                
                # base64로 인코딩된 엑셀 데이터를 디코딩
                excel_content = base64.b64decode(file_data.get('content'))
                # BytesIO 객체로 변환
                excel_file = BytesIO(excel_content)
                
                # ExcelService를 사용하여 데이터 읽기
                df = self.excel_service.read_excel_data(excel_file)
                if df is not None:
                    logger.info(f"엑셀 데이터 읽기 성공. 데이터 크기: {df.shape}")
                    # 데이터 요약 정보 생성
                    summary = self.excel_service.get_excel_summary(df)
                    
                    return {
                        'command': 'excel_summary',
                        'summary': summary,
                        'status': 'success'
                    }
                else:
                    return {
                        'command': 'excel_summary',
                        'message': '엑셀 파일을 읽는 중 오류가 발생했습니다.',
                        'status': 'error'
                    }
            else:
                return {
                    'command': 'excel_summary',
                    'message': '지원하지 않는 파일 형식입니다.',
                    'status': 'error'
                }
        except Exception as e:
            logger.error(f"엑셀 파일 처리 중 오류 발생: {str(e)}")
            return {
                'command': 'excel_summary',
                'message': f'엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}',
                'status': 'error'
            } 