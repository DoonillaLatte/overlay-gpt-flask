from flask import Flask
from flask_socketio import SocketIO
from prompts.prompt_factory import PromptFactory
import json
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from embedding.embedder import Embedding

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
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
prompt_factory = PromptFactory()

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('prompt_request')
def handle_prompt_request(data: Dict[str, Any]):
    try:
        logger.debug(f"Raw request data: {data}")
        
        # 데이터 검증
        request = PromptRequest(**data)
        logger.info(f"Received prompt request: {request.dict()}")
        
        # request_type에 따라 적절한 프롬프트 전략 선택
        strategy_name = {
            1: "explain",
            2: "freestyle",
            3: "generate_text",
            4: "summary"
        }.get(request.request_type, "explain")
        
        logger.info(f"Selected strategy: {strategy_name}")
        
        # 프롬프트 전략 생성 및 실행
        strategy = prompt_factory.get_strategy(strategy_name)
        response = strategy.generate_prompt(request.dict())
        
        logger.info(f"Generated response for chat_id: {request.chat_id}")
        
        # 응답 전송
        socketio.emit('prompt_response', {
            'chat_id': request.chat_id,
            'response': response,
            'status': 'success'
        })
        logger.debug("Response sent successfully")

        # 받은 데이터 임베딩
        embedding = Embedding()
        embedding.embedding_text(request.dict())
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        # 에러 발생 시 에러 메시지 전송
        socketio.emit('prompt_response', {
            'chat_id': data.get('chat_id', -1),
            'response': str(e),
            'status': 'error'
        })
        logger.debug("Error response sent")

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    socketio.run(app, debug=True, port=5000)
