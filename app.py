from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from prompts.prompt_factory import PromptFactory
import json
import logging
from typing import Dict, Any
from pydantic import BaseModel
from services.vector_db_service import VectorDBService
from services.command_handler import CommandHandler
from prompts.strategies.memory_manager import MemoryManager
from config_loader import config

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

# 서비스 인스턴스 생성
prompt_factory = PromptFactory()
vector_db_service = VectorDBService(storage_dir="data/vector_db")
command_handler = CommandHandler(vector_db_service=vector_db_service, prompt_factory=prompt_factory)

# 메모리 매니저 초기화
MemoryManager.initialize(base_dir="data/memory")
logger.info("메모리 매니저가 초기화되었습니다.")

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('message')
def handle_message(message):
    try:
        # 요청 시간과 횟수 추적
        import datetime
        request_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        logger.info(f'[{request_time}] ========== Flask 메시지 수신 시작 ==========')
        logger.info(f'[{request_time}] Received message: {message}')
        logger.info(f'[{request_time}] Message type: {type(message)}')
        
        if isinstance(message, str):
            message = json.loads(message)
            
        logger.info(f'[{request_time}] Processing message with command: {message.get("command")}')
        logger.info(f'[{request_time}] Chat ID: {message.get("chat_id")}')
        logger.info(f'[{request_time}] Prompt: {message.get("prompt", "N/A")[:100]}...')  # 처음 100자만
        
        # CommandHandler를 통해 메시지 처리
        response = command_handler.handle_command(message)
        logger.info(f'[{request_time}] Generated response command: {response.get("command")}')
        logger.info(f'[{request_time}] Response status: {response.get("status")}')
        logger.info(f'[{request_time}] Response length: {len(str(response.get("message", "")))}')
        
        logger.info(f'[{request_time}] ========== Flask 응답 전송 시작 ==========')
        
        # 메시지를 보낸 클라이언트에게만 응답 (broadcast=False로 변경)
        emit('message_response', response)
        logger.info(f'[{request_time}] ========== Flask 응답 전송 완료 ==========')
            
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}", exc_info=True)
        error_response = {
            'command': 'response_single_generated_response',
            'message': str(e),
            'status': 'error'
        }
        socketio.emit('message_response', error_response)
        logger.error(f"Error response sent: {error_response}")

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # 설정 검증
    if not config.is_api_key_valid():
        logger.error("❌ OpenAI API 키가 올바르지 않습니다!")
        logger.error("설치 프로그램에서 입력한 API 키를 확인해주세요.")
        logger.error("또는 config.json 파일에서 직접 설정할 수 있습니다.")
        input("계속하려면 Enter를 누르세요...")
    else:
        logger.info("✅ OpenAI API 키가 설정되었습니다.")
    
    logger.info("Starting Flask application...")
    
    # 설정에서 포트 가져오기
    port = config.get_flask_port()
    debug_mode = config.get_flask_env() == 'development'
    
    logger.info(f"서버 포트: {port}")
    logger.info(f"디버그 모드: {debug_mode}")
    
    socketio.run(app, debug=debug_mode, port=port, host='0.0.0.0')
