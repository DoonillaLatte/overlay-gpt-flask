from flask import Flask, render_template
from flask_socketio import SocketIO
from prompts.prompt_factory import PromptFactory
import json
import logging
from typing import Dict, Any
from pydantic import BaseModel, Field
from services.vector_db_service import VectorDBService
from services.excel_service import ExcelService
import base64
import pandas as pd
from io import BytesIO

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
            
            # 파일 데이터가 있는 경우 엑셀 데이터 읽기
            if 'file_data' in message:
                file_data = message['file_data']
                if file_data.get('content_type') == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                    logger.info(f"엑셀 파일 처리 시작: {file_data.get('filename')}")
                    try:
                        # base64로 인코딩된 엑셀 데이터를 디코딩
                        excel_content = base64.b64decode(file_data.get('content'))
                        # BytesIO 객체로 변환
                        excel_file = BytesIO(excel_content)
                        # ExcelService를 사용하여 데이터 읽기
                        df = ExcelService.read_excel_data(excel_file)
                        if df is not None:
                            logger.info(f"엑셀 데이터 읽기 성공. 데이터 크기: {df.shape}")
                            logger.info(f"컬럼 목록: {df.columns.tolist()}")
                            # 데이터 요약 정보 생성
                            summary = ExcelService.get_excel_summary(df)
                            logger.info(f"엑셀 데이터 요약:\n{json.dumps(summary, indent=2, ensure_ascii=False)}")
                            socketio.emit('message_response',  {
                                'command': 'excel_summary',
                                'summary': summary,
                                'status': 'success'
                            })
                        else:
                            logger.error("엑셀 데이터 읽기 실패")
                            socketio.emit('message_response', {
                                'command': 'excel_summary',
                                'message': '엑셀 파일을 읽는 중 오류가 발생했습니다.',
                                'status': 'error'
                            })
                    except Exception as e:
                        logger.error(f"엑셀 파일 처리 중 오류 발생: {str(e)}")
                        socketio.emit('message_response', {
                            'command': 'excel_summary',
                            'message': f'엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}',
                            'status': 'error'
                        })
            
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
            else:
                # 다중 프로그램 프롬프트 요청 처리
                if command == 'search_similar_context':
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
                        #파일 식별번호
                        multi_program_id = request.target_program.id
                        #파일 타입
                        multi_program_type = request.target_program.type
                        #파일 컨텍스트
                        multi_program_context = request.target_program.context
                        
                        # 벡터 데이터베이스에 프로그램 정보 저장
                        try:
                            vector_db_service.store_program_info(
                                program_id=multi_program_id,
                                program_type=multi_program_type,
                                program_context=multi_program_context
                            )
                        except Exception as e:
                            logger.error(f"벡터 DB 저장 중 오류 발생: {str(e)}")
                            raise
                        
                        # 유사한 프로그램 검색
                        try:
                            similar_programs = vector_db_service.search_similar_programs(
                                query=multi_program_context,
                                k=5
                            )
                            logger.info(f"유사한 프로그램 검색 완료. 결과 수: {len(similar_programs)}")
                            print(similar_programs)
                            # 검색된 프로그램 정보 출력
                            for program in similar_programs:
                                logger.info(f"유사한 프로그램: ID={program['id']}, 타입={program['metadata']['type']}, 컨텍스트={program['metadata']['context']}")
                            
                        except Exception as e:
                            logger.error(f"유사한 프로그램 검색 중 오류 발생: {str(e)}")
                            raise
                        
                        # 검색된 프로그램 정보를 프롬프트에 포함
                        # 유사한 프로그램의 ID 리스트 추출
                        similar_program_ids = [program['id'] for program in similar_programs]
                        
                        # ID 리스트를 포함한 응답 전송
                        socketio.emit('message_response', {
                            'command': 'search_similar_context',
                            'similar_program_ids': similar_program_ids,
                            'status': 'success'
                        })
                        
                    except Exception as e:
                        socketio.emit('message_response', {
                            'command': 'search_similar_context',
                            'message': f'유사한 프로그램 검색 중 오류 발생: {str(e)}',
                            'status': 'error'
                        })
                        
                elif command == 'run_convert_prompt':
                    # 프롬프트 요청 처리
                    try:
                        strategy = prompt_factory.get_strategy(request.request_type)
                        response = strategy.generate_prompt(request.dict())
                        
                        socketio.emit('message_response', {
                            'command': 'response_multiple_generated_response',
                            'message': response,
                            'status': 'success'
                        })
                    except Exception as e:
                        socketio.emit('message_response', {
                            'command': 'response_multiple_generated_response',
                            'message': f'프롬프트 처리 중 오류 발생: {str(e)}',
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

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    logger.info("Starting Flask application...")
    socketio.run(app, debug=True, port=5001, host='0.0.0.0')
