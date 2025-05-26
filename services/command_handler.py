from typing import Dict, Any
import logging
from .vector_db_service import VectorDBService
from databases.vector_database import VectorDatabase
from .excel_service import ExcelService
from prompts.prompt_factory import PromptFactory

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
                'request_single_generated_response': self._handle_response,
                'request_top_workflows': self._handle_request_top_workflows
            }
            
            # 매핑된 핸들러 실행
            handler = command_handlers.get(command)
            if handler:
                return handler(message)
            else:
                return {
                    'command': f'response_for_{command}',
                    'message': f'지원하지 않는 명령어입니다: {command}',
                    'status': 'error'
                }
                
        except Exception as e:
            logger.error(f"명령어 처리 중 오류 발생: {str(e)}", exc_info=True)
            return {
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
            
            # 필수 필드 검증
            if not content['prompt']:
                raise ValueError("prompt는 필수 입력값입니다.")
            if not content['request_type']:
                raise ValueError("request_type은 필수 입력값입니다.")
            
            # target_program이 있는 경우 convert_prompt 사용
            if content.get('target_program'):
                strategy_name = "convert_prompt"
            else:
                strategy_name = {
                    1: "freestyle",
                    2: "generate_text",
                    3: "explain",
                    4: "summary"
                }.get(content['request_type'], "freestyle")
            
            strategy = self.prompt_factory.get_strategy(strategy_name)
            response = strategy.generate_prompt(content)
            
            # 제목 생성
            title = self.vector_db_service._vector_db._generate_title(content['prompt'])
            
            return {
                'command': f'response_for_{strategy_name}',
                'title': title,
                'message': response,
                'status': 'success'
            }
        except ValueError as e:
            logger.error(f"잘못된 요청: {str(e)}")
            return {
                'command': 'response_error',
                'message': str(e),
                'status': 'error'
            }
        except Exception as e:
            logger.error(f"응답 생성 중 오류 발생: {str(e)}")
            return {
                'command': 'response_error',
                'message': f'처리 중 오류가 발생했습니다: {str(e)}',
                'status': 'error'
            }

    def _handle_request_top_workflows(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """유사 컨텍스트 검색 처리"""
        try:
            content = {
                'chat_id': message.get('chat_id'),
                'prompt': message.get('prompt'),
                'request_type': message.get('request_type'),
                'current_program': message.get('current_program')
            }
            
            multi_program_id = content['current_program']['fileId']
            multi_program_type = content['current_program']['fileType']
            multi_program_context = content['current_program']['context']
            
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
                'command': 'response_top_workflows',
                'similar_program_ids': similar_program_ids,
                'status': 'success'
            }
        except Exception as e:
            logger.error(f"유사 컨텍스트 검색 중 오류 발생: {str(e)}")
            return {
                'command': 'response_top_workflows',
                'message': f'유사한 프로그램 검색 중 오류 발생: {str(e)}',
                'status': 'error'
            }