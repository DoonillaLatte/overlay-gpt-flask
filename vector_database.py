import numpy as np
import faiss
from typing import Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, dimension: int = 768):
        """
        벡터 데이터베이스를 초기화합니다.
        
        Args:
            dimension (int): 벡터의 차원 수 (기본값: 768)
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata_store = {}
        # 한국어 텍스트에 최적화된 모델 사용
        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        
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
        
    def store_vector(self, id: int, text: str, metadata: Dict[str, Any]) -> None:
        """
        벡터를 저장합니다.
        
        Args:
            id (int): 벡터 ID
            text (str): 텍스트 데이터
            metadata (Dict[str, Any]): 메타데이터
        """
        # 텍스트를 벡터로 변환
        vector = self._get_embedding(text)
        
        # 벡터 저장
        self.index.add(vector)
        
        # 메타데이터 저장
        self.metadata_store[id] = {
            "text": text,
            "metadata": metadata
        }
        
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
        
    def search_similar(self, query: str, k: int = 5) -> list:
        """
        유사한 벡터를 검색합니다.
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수
            
        Returns:
            list: 유사한 벡터들의 메타데이터 리스트
        """
        # 쿼리 텍스트를 벡터로 변환
        query_vector = self._get_embedding(query)
        
        # 유사도 검색
        distances, indices = self.index.search(query_vector, k)
        
        # 결과 반환
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # -1은 검색 결과가 없는 경우
                result = self.metadata_store[idx].copy()
                result['similarity_score'] = float(1 / (1 + distances[0][i]))  # 거리를 유사도 점수로 변환
                results.append(result)
                
        return results 