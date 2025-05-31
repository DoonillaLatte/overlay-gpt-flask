import numpy as np
import faiss
from typing import Dict, Any, Optional, List
from sentence_transformers import SentenceTransformer
import logging
import os
import json
import pickle
from openai import OpenAI
from dotenv import load_dotenv
from collections import OrderedDict

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, dimension: int = 768, storage_dir: str = "vector_db", max_vectors: int = 1000):
        """
        벡터 데이터베이스를 초기화합니다.
        
        Args:
            dimension (int): 벡터의 차원 수 (기본값: 768)
            storage_dir (str): 벡터 데이터베이스 저장 디렉토리 (기본값: "vector_db")
            max_vectors (int): 최대 저장 벡터 수 (기본값: 1000)
        """
        self.dimension = dimension
        self.storage_dir = storage_dir
        self.index_path = os.path.join(storage_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(storage_dir, "metadata.json")
        self.max_vectors = max_vectors
        
        # OpenAI 클라이언트 초기화
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # 저장 디렉토리가 없으면 생성
        os.makedirs(storage_dir, exist_ok=True)
        
        # 기존 인덱스가 있으면 로드, 없으면 새로 생성
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                self.metadata_store = json.load(f)
        else:
            self.index = faiss.IndexFlatL2(dimension)
            self.metadata_store = {}
            
        # 한국어 텍스트에 최적화된 모델 사용
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')

    def _generate_title(self, text: str, max_words: int = 5) -> str:
        """
        텍스트의 내용을 대표하는 간단한 제목을 생성합니다.
        
        Args:
            text (str): 원본 텍스트
            max_words (int): 제목의 최대 단어 수 (기본값: 5)
            
        Returns:
            str: 생성된 제목
        """
        try:
            prompt = f"""다음 텍스트의 내용을 가장 잘 표현하는 간단한 제목을 만들어주세요.
            
            조건:
            1. 최대 {max_words}개의 단어로 구성
            2. 명사구나 짧은 문장 형태로 작성
            3. 텍스트의 핵심 의도나 목적을 포함
            4. 가능한 한 구체적으로 표현
            5. 제목만 출력 (다른 설명 없이)
            
            텍스트:
            {text}
            
            제목:"""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 텍스트의 핵심을 정확하게 파악하여 간단한 제목으로 만드는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )

            # 응답에서 제목 추출 및 정리
            title = response.choices[0].message.content.strip()
            logger.info(f"생성된 제목: {title}")
            return title
            
        except Exception as e:
            logger.error(f"제목 생성 중 오류 발생: {str(e)}")
            return ""
        
    def _save_to_disk(self) -> None:
        """
        벡터 데이터베이스를 디스크에 저장합니다.
        """
        try:
            # FAISS 인덱스 저장
            faiss.write_index(self.index, self.index_path)
            
            # 메타데이터 저장
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_store, f, ensure_ascii=False, indent=2)
                
            logger.info(f"벡터 데이터베이스가 {self.storage_dir}에 저장되었습니다.")
        except Exception as e:
            logger.error(f"벡터 데이터베이스 저장 중 오류 발생: {str(e)}")
            raise
        
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        텍스트를 벡터로 변환합니다.
        
        Args:
            text (str): 변환할 텍스트
            
        Returns:
            np.ndarray: 변환된 벡터
        """
        try:
            embedding = self.model.encode(text)
            return embedding.reshape(1, -1).astype('float32')
        except Exception as e:
            logger.error(f"텍스트 임베딩 중 오류 발생: {str(e)}")
            raise
        
    def _remove_oldest_vector(self) -> None:
        """
        가장 오래된 벡터를 삭제합니다.
        """
        if not self.metadata_store:
            return

        # 가장 오래된 ID 찾기
        oldest_id = min(self.metadata_store.keys(), key=lambda x: int(x))
        
        # 메타데이터에서 삭제
        del self.metadata_store[oldest_id]
        
        # FAISS 인덱스 재구성
        if len(self.metadata_store) > 0:
            # 새로운 인덱스 생성
            new_index = faiss.IndexFlatL2(self.dimension)
            
            # 남은 벡터들을 새 인덱스에 추가
            remaining_ids = sorted(self.metadata_store.keys(), key=lambda x: int(x))
            for id in remaining_ids:
                text = self.metadata_store[id]["text"]
                vector = self._get_embedding(text)
                new_index.add(vector)
            
            # 기존 인덱스 교체
            self.index = new_index
        else:
            # 모든 벡터가 삭제된 경우 새 인덱스 생성
            self.index = faiss.IndexFlatL2(self.dimension)
        
        logger.info(f"가장 오래된 벡터가 삭제되었습니다. ID: {oldest_id}")

    def store_vector(self, id: int, text: str, metadata: Dict[str, Any]) -> None:
        """
        벡터를 저장합니다. 최대 저장 개수를 초과하면 가장 오래된 벡터를 삭제합니다.
        
        Args:
            id (int): 벡터 ID
            text (str): 텍스트 데이터
            metadata (Dict[str, Any]): 메타데이터
        """
        # 최대 저장 개수 확인
        if len(self.metadata_store) >= self.max_vectors:
            self._remove_oldest_vector()
        
        # 텍스트에서 제목 생성
        title = self._generate_title(text)
        
        # 제목만 벡터화
        vector = self._get_embedding(title)
        
        # 벡터 저장
        self.index.add(vector)
        
        # 메타데이터 저장 (제목 정보 포함)
        self.metadata_store[id] = {
            "text": text,
            "title": title,
            "metadata": metadata
        }
        
        # 디스크에 저장
        self._save_to_disk()
        
    def get_vector(self, id: int) -> Dict[str, Any]:
        """
        벡터를 조회합니다.
        
        Args:
            id (int): 벡터 ID
            
        Returns:
            Dict[str, Any]: 저장된 벡터 데이터
        """
        if id not in self.metadata_store:
            raise KeyError(f"ID {id}에 해당하는 벡터가 존재하지 않습니다.")
            
        return self.metadata_store[id]
        
    def delete_vector(self, id: int) -> None:
        """
        벡터를 삭제합니다.
        
        Args:
            id (int): 벡터 ID
        """
        if id not in self.metadata_store:
            raise KeyError(f"ID {id}에 해당하는 벡터가 존재하지 않습니다.")
            
        del self.metadata_store[id]
        # 디스크에 저장
        self._save_to_disk()
        
    def search_similar(self, query: str, k: int = 5) -> list:
        """
        유사한 벡터를 검색합니다.
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수
            
        Returns:
            list: 유사한 벡터들의 메타데이터 리스트
        """
        try:
            if len(self.metadata_store) == 0:
                return []

            # 쿼리에서 제목 생성
            query_title = self._generate_title(query)
            
            # 쿼리 제목과 원본 쿼리를 결합하여 벡터화
            combined_query = f"{query_title} {query}"
            query_vector = self._get_embedding(combined_query)
            
            # 실제 저장된 벡터 수에 맞춰 k 값 조정
            k = min(k, len(self.metadata_store))
            
            # 유사도 검색
            distances, indices = self.index.search(query_vector, k)
            
            # 결과 반환
            results = []
            metadata_ids = list(self.metadata_store.keys())
            
            for i, idx in enumerate(indices[0]):
                if idx != -1 and idx < len(metadata_ids):  # 유효한 인덱스인지 확인
                    metadata_id = metadata_ids[idx]
                    result = {
                        "id": metadata_id,
                        "text": self.metadata_store[metadata_id]["text"],
                        "title": self.metadata_store[metadata_id]["title"],
                        "metadata": self.metadata_store[metadata_id]["metadata"],
                        "similarity_score": float(1 / (1 + distances[0][i])),
                        "fileId": self.metadata_store[metadata_id]["metadata"].get("fileId", None),
                        "volumeId": self.metadata_store[metadata_id]["metadata"].get("volumeId", None)
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"유사 벡터 검색 중 오류 발생: {str(e)}")
            return [] 