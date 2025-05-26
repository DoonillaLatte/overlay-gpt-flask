from flask import Flask, render_template
from flask_socketio import SocketIO
from prompts.prompt_factory import PromptFactory
import json
import logging
from typing import Dict, Any
from pydantic import BaseModel
from services.vector_db_service import VectorDBService
from services.command_handler import CommandHandler

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
            
        logger.info(f'Processing message with command: {message.get("command")}')
        
        # CommandHandler를 통해 메시지 처리
        response = command_handler.handle_command(message)
        logger.info(f'Generated response: {response}')
        
        socketio.emit('message_response', response)
        logger.info("Message response sent successfully")
            
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
    logger.info("Starting Flask application...")
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
