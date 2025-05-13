from flask import Flask
from flask_socketio import SocketIO, emit
from registry import load_prompts, prompt_registry
from prompt_service import handle_prompt

app = Flask(__name__)
app.config['SECRET_KEY'] = None
socketio = SocketIO(app, cors_allowed_origins="*")  # CORS 허용

load_prompts()

@socketio.on('prompt_request')
def on_prompt(data):
    chat_id = data.get("chat_id")
    prompt_request = data.get("prompt")
    current_program = data.get("current_program")
    target_program = data.get("target_program")
    
    print(f"Received from .NET: {data}")
    result = handle_prompt(prompt_request, current_program, target_program)
    emit('prompt_response', {'result': result})

if __name__ == '__main__':
    socketio.run(app, debug=True)
