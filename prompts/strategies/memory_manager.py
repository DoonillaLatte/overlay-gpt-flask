from langchain.memory import ConversationBufferMemory

class MemoryManager:
    """
    모든 프롬프트 전략 클래스가 공유하는 메모리 관리 클래스
    """
    _instance = None
    _memory = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryManager, cls).__new__(cls)
            # 단일 메모리 인스턴스 생성
            cls._memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        return cls._instance

    @classmethod
    def get_memory(cls) -> ConversationBufferMemory:
        """
        공유 메모리를 가져옵니다.
        
        Returns:
            ConversationBufferMemory: 대화 메모리
        """
        if cls._memory is None:
            cls._memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
        return cls._memory

    @classmethod
    def clear_memory(cls):
        """
        메모리를 초기화합니다.
        """
        cls._memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        ) 