from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
import json
import os

class Embedding():
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    def embedding_text(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # 필요 정보 추출
        program_id = request_data.get('chat_id', {})
        current_program = request_data.get('current_program', {})
        target_program = request_data.get('target_program', {})
        context = current_program.get('context', '')

        if not context:
            raise ValueError("current_program.context is required for embedding.")

        # 현재 context 벡터화
        embedded_query: List[float] = self.embeddings.embed_query(context)

        # embedding된 context 데이터와 current, target프로그램 db로 전달
        data_to_save = {
            "embedding": embedded_query,
            "current_program_type": current_program.get('type', ''),
            "target_program_type": target_program.get('type', '')
        }

        # 데이터 임베딩
        self.save_embedding_to_file(program_id, data_to_save)

    #아직 db모델을 몰라서 일단은 대충 json파일로 저장하는걸로 만들어 놓음
    def save_embedding_to_file(self, id: int, data: Dict[str, Any]):
        # 파일 식별을 고유 id로 하게 설정, 현재 위치에 넣게 설정(일단)
        path = os.path.join("embeddings_cache", id)

        os.makedirs("embeddings_cache", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
