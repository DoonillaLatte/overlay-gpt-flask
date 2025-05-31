from typing import Dict, Any
import logging
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
                'request_top_workflows': self._handle_request_top_workflows
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
            
            response = strategy.generate_prompt(content)
            
            # 제목 생성
            title = None
            file_type = 'excel'  # 기본값으로 excel 사용
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