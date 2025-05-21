from flask import Flask, render_template
from flask_socketio import SocketIO
from prompts.prompt_factory import PromptFactory
import json
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

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

# @socketio.on('prompt_request')
# def handle_prompt_request(data: Dict[str, Any]):
#     try:
#         logger.debug(f"Raw request data: {data}")
        
#         # 데이터 검증
#         request = PromptRequest(**data)
#         logger.info(f"Received prompt request: {request.dict()}")
        
#         # request_type에 따라 적절한 프롬프트 전략 선택
#         strategy_name = {
#             1: "explain",
#             2: "freestyle",
#             3: "generate_text",
#             4: "summary"
#         }.get(request.request_type, "explain")
        
#         logger.info(f"Selected strategy: {strategy_name}")
        
#         # 프롬프트 전략 생성 및 실행
#         strategy = prompt_factory.get_strategy(strategy_name)
#         response = strategy.generate_prompt(request.dict())
        
#         logger.info(f"Generated response for chat_id: {request.chat_id}")
        
#         # 응답 전송
#         socketio.emit('prompt_response', {
#             'chat_id': request.chat_id,
#             'response': response,
#             'status': 'success'
#         })
#         logger.debug("Response sent successfully")
        
#     except Exception as e:
#         logger.error(f"Error processing request: {str(e)}", exc_info=True)
#         # 에러 발생 시 에러 메시지 전송
#         socketio.emit('prompt_response', {
#             'chat_id': data.get('chat_id', -1),
#             'response': str(e),
#             'status': 'error'
#         })
#         logger.debug("Error response sent")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
