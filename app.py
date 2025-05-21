from flask import Flask, render_template
from flask_socketio import SocketIO
from prompts.prompt_factory import PromptFactory
import json
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from services.vector_db_service import VectorDBService

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 요청 데이터 모델
class ProgramInfo(BaseModel):
    id: int
    type: str
    context: str

class PromptRequest(BaseModel):
    chat_id: int
    prompt: str
    request_type: int
    description: str
    current_program: ProgramInfo
    target_program: ProgramInfo

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, async_mode='threading')
prompt_factory = PromptFactory()

# VectorDBService 인스턴스 생성
vector_db_service = VectorDBService()

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('message')
def handle_message(message):
    try:
        logger.info(f'Received message: {message}')
        
        if isinstance(message, str):
            message = json.loads(message)
        
        # JSON 형식 검증
        if isinstance(message, dict) and 'command' in message:
            command = message['command']
            content = message.get('content', {})
            target_program = message.get('target_program', None)
            current_program = message.get('current_program', None)
            
            if target_program is None:
                if command == 'request_single_generated_response':
                    # 프롬프트 요청 처리
                    try:
                        # content 객체 생성
                        content = {
                            'chat_id': message.get('chat_id'),
                            'prompt': message.get('prompt'),
                            'request_type': message.get('request_type'),
                            'description': message.get('description'),
                            'current_program': message.get('current_program'),
                            'target_program': message.get('target_program')
                        }
                        
                        request = PromptRequest(**content)
                        strategy_name = {
                            1: "explain",
                            2: "freestyle",
                            3: "generate_text",
                            4: "summary"
                        }.get(request.request_type, "explain")
                        
                        strategy = prompt_factory.get_strategy(strategy_name)
                        response = strategy.generate_prompt(request.dict())
                        
                        socketio.emit('message_response', {
                            'command': 'response_single_generated_response',
                            'message': response,
                            'status': 'success'
                        })
                    except Exception as e:
                        socketio.emit('message_response', {
                            'command': 'response_single_generated_response',
                            'message': f'프롬프트 처리 중 오류 발생: {str(e)}',
                            'status': 'error'
                        })
                else:
                    socketio.emit('message_response', {
                        'command': 'response_single_generated_response',
                        'message': f'지원하지 않는 명령어입니다: {command}',
                        'status': 'error'
                    })
            # else:
            #     # 다중 프로그램 프롬프트 요청 처리
            #     try:
            #         # content 객체 생성
            #         content = {
            #             'chat_id': message.get('chat_id'),
            #             'prompt': message.get('prompt'),
            #             'request_type': message.get('request_type'),
            #             'description': message.get('description'),
            #             'current_program': message.get('current_program'),
            #             'target_program': message.get('target_program')
            #         }
                    
            #         request = PromptRequest(**content)
            #         #파일 식별번호
            #         multi_program_id = request.target_program.id
            #         #파일 타입
            #         multi_program_type = request.target_program.type
            #         #파일 컨텍스트
            #         multi_program_context = request.target_program.context
                    
            #         # 벡터 데이터베이스에 프로그램 정보 저장
            #         try:
            #             vector_db_service.store_program_info(
            #                 program_id=multi_program_id,
            #                 program_type=multi_program_type,
            #                 program_context=multi_program_context
            #             )
            #         except Exception as e:
            #             logger.error(f"벡터 DB 저장 중 오류 발생: {str(e)}")
            #             raise
                    
            #         # 유사한 프로그램 검색
            #         try:
            #             similar_programs = vector_db_service.search_similar_programs(
            #                 query=multi_program_context,
            #                 k=5
            #             )
            #             logger.info(f"유사한 프로그램 검색 완료. 결과 수: {len(similar_programs)}")
                        
            #             # 검색된 프로그램 정보 출력
            #             for program in similar_programs:
            #                 logger.info(f"유사한 프로그램: ID={program['id']}, 타입={program['type']}, 컨텍스트={program['context']}")
                        
            #         except Exception as e:
            #             logger.error(f"유사한 프로그램 검색 중 오류 발생: {str(e)}")
            #             raise
                    
            #         # 검색된 프로그램 정보를 프롬프트에 포함
            #         prompt_with_similar_programs = f"{request.prompt}\n\n유사한 프로그램:\n{similar_programs}"
                    
            #         # 프롬프트 요청 처리
            #         try:
            #             strategy = prompt_factory.get_strategy(request.request_type)
            #             response = strategy.generate_prompt(request.dict())
                        
            #             socketio.emit('message_response', {
            #                 'command': 'response_single_generated_response',
            #                 'message': response,
            #                 'status': 'success'
            #             })
            #         except Exception as e:
            #             socketio.emit('message_response', {
            #                 'command': 'response_single_generated_response',
            #                 'message': f'프롬프트 처리 중 오류 발생: {str(e)}',
            #                 'status': 'error'
            #             })
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
            #     except Exception as e:
            #         socketio.emit('message_response', {
            #             'command': 'response_single_generated_response',
            #             'message': f'프롬프트 처리 중 오류 발생: {str(e)}',
            #             'status': 'error'
            #         })
        else:
            # 일반 메시지 처리
            socketio.emit('message_response', {
                'command': 'response_single_generated_response',
                'message': message,
                'status': 'success'
            })
            
        logger.debug("Message response sent successfully")
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        socketio.emit('message_response', {
            'message': str(e),
            'status': 'error'
        })
        logger.debug("Error response sent")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    socketio.run(app, debug=True, port=5000, host='0.0.0.0')
