from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from typing import List, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    모든 프롬프트 전략 클래스가 공유하는 메모리 관리 클래스
    """
    _instance = None
    _memory = None
    _memory_file = "memory.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryManager, cls).__new__(cls)
            # 단일 메모리 인스턴스 생성
            cls._memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            # 저장된 메모리가 있다면 로드
            cls._load_memory()
        return cls._instance

    @classmethod
    def get_memory(cls) -> ConversationBufferMemory:
        """
        공유 메모리를 가져옵니다.
        
        Returns:
            ConversationBufferMemory: 대화 메모리
        """
        if cls._instance is None:
            cls()
        return cls._memory

    @classmethod
    def clear_memory(cls):
        """
        메모리를 초기화합니다.
        """
        if cls._instance is None:
            cls()
        cls._memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        # 메모리 파일 삭제
        if os.path.exists(cls._memory_file):
            os.remove(cls._memory_file)

    @classmethod
    def _load_memory(cls):
        """
        저장된 메모리를 로드합니다.
        """
        try:
            if os.path.exists(cls._memory_file):
                with open(cls._memory_file, 'r', encoding='utf-8') as f:
                    memory_data = json.load(f)
                    if memory_data:
                        # 메모리 데이터를 메시지로 변환
                        messages = []
                        for msg in memory_data:
                            if msg.get('type') == 'human':
                                messages.append(('human', msg.get('content', '')))
                            elif msg.get('type') == 'ai':
                                messages.append(('ai', msg.get('content', '')))
                        # 메모리에 메시지 추가
                        for role, content in messages:
                            cls._memory.chat_memory.add_message(
                                BaseMessage(content=content, type=role)
                            )
        except Exception as e:
            logger.error(f"메모리 로드 중 오류 발생: {str(e)}")

    @classmethod
    def _save_memory(cls):
        """
        현재 메모리를 저장합니다.
        """
        try:
            # 메모리 데이터를 JSON 형식으로 변환
            memory_data = []
            for message in cls._memory.chat_memory.messages:
                memory_data.append({
                    'type': message.type,
                    'content': message.content
                })
            # 메모리 파일에 저장
            with open(cls._memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"메모리 저장 중 오류 발생: {str(e)}")

    @classmethod
    def add_message(cls, message: BaseMessage):
        """
        메모리에 메시지를 추가합니다.
        
        Args:
            message (BaseMessage): 추가할 메시지
        """
        if cls._instance is None:
            cls()
        cls._memory.chat_memory.add_message(message)
        cls._save_memory()

    @classmethod
    def get_messages(cls) -> List[BaseMessage]:
        """
        저장된 모든 메시지를 가져옵니다.
        
        Returns:
            List[BaseMessage]: 메시지 리스트
        """
        if cls._instance is None:
            cls()
        return cls._memory.chat_memory.messages 