import numpy as np
import faiss
from typing import Dict, Any, Optional, List, Tuple
from sentence_transformers import SentenceTransformer
import logging
import os
import json
import pickle
from datetime import datetime
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, dimension: int = 768, storage_dir: str = "vector_db", model_name: str = "jhgan/ko-sroberta-multitask"):
        """
        벡터 데이터베이스를 초기화합니다.
        
        Args:
            dimension (int): 벡터의 차원 수 (기본값: 768)
            storage_dir (str): 벡터 데이터베이스 저장 디렉토리 (기본값: "vector_db")
            model_name (str): 사용할 임베딩 모델 이름 (기본값: "jhgan/ko-sroberta-multitask")
        """
        if dimension <= 0:
            raise ValueError("차원 수는 양수여야 합니다.")
            
        self.dimension = dimension
        self.storage_dir = storage_dir
        self.index_path = os.path.join(storage_dir, "faiss_index.bin")
        self.metadata_path = os.path.join(storage_dir, "metadata.json")
        self.id_map_path = os.path.join(storage_dir, "id_map.pkl")
        
        # 디렉토리 생성
        os.makedirs(storage_dir, exist_ok=True)
        
        # 임베딩 모델 초기화
        try:
            self.model = SentenceTransformer(model_name)
            actual_dim = self.model.get_sentence_embedding_dimension()
            if actual_dim != dimension:
                raise ValueError(f"모델의 임베딩 차원({actual_dim})이 지정된 차원({dimension})과 다릅니다.")
        except Exception as e:
            logger.error(f"임베딩 모델 초기화 실패: {str(e)}")
            raise
            
        # FAISS 인덱스 초기화
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata: Dict[int, Dict[str, Any]] = {}
        self.id_to_index: Dict[int, int] = {}
        self.next_index = 0
        
        # 기존 데이터 로드
        self._load_data()

    def _load_data(self):
        """저장된 데이터를 로드합니다."""
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
            if os.path.exists(self.metadata_path):
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            if os.path.exists(self.id_map_path):
                with open(self.id_map_path, "rb") as f:
                    self.id_to_index = pickle.load(f)
                if self.id_to_index:
                    self.next_index = max(self.id_to_index.values()) + 1
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {str(e)}")
            # 초기 상태로 리셋
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = {}
            self.id_to_index = {}
            self.next_index = 0

    def store_vector(self, id: int, text: str, metadata: Dict[str, Any]) -> bool:
        """
        텍스트를 벡터로 변환하여 저장합니다.
        
        Args:
            id (int): 벡터의 고유 ID
            text (str): 임베딩할 텍스트
            metadata (Dict[str, Any]): 벡터와 관련된 메타데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 텍스트 임베딩
            vector = self.model.encode([text])[0]
            if len(vector) != self.dimension:
                raise ValueError(f"임베딩 차원({len(vector)})이 예상 차원({self.dimension})과 다릅니다.")

            # 벡터 정규화
            vector = vector.reshape(1, -1)
            faiss.normalize_L2(vector)

            # 인덱스에 추가
            self.index.add(vector)
            self.metadata[id] = metadata
            self.id_to_index[id] = self.next_index
            self.next_index += 1

            # 상태 저장
            self._save_state()
            return True
        except Exception as e:
            logger.error(f"벡터 저장 중 오류 발생: {str(e)}")
            return False

    def search_similar(self, text: str, k: int = 5) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        주어진 텍스트와 가장 유사한 벡터들을 검색합니다.
        
        Args:
            text (str): 검색할 텍스트
            k (int): 반환할 결과 수 (기본값: 5)
            
        Returns:
            List[Tuple[int, float, Dict[str, Any]]]: (ID, 유사도 점수, 메타데이터) 튜플의 리스트
        """
        try:
            # 텍스트 임베딩
            query_vector = self.model.encode([text])[0]
            query_vector = query_vector.reshape(1, -1)
            faiss.normalize_L2(query_vector)

            # 유사도 검색
            distances, indices = self.index.search(query_vector, k)
            
            # 결과 매핑
            results = []
            for distance, idx in zip(distances[0], indices[0]):
                if idx != -1:  # 유효한 인덱스인 경우
                    # 인덱스로부터 원본 ID 찾기
                    original_id = None
                    for id, index in self.id_to_index.items():
                        if index == idx:
                            original_id = id
                            break
                    
                    if original_id is not None and original_id in self.metadata:
                        results.append((original_id, float(distance), self.metadata[original_id]))

            return results
        except Exception as e:
            logger.error(f"유사도 검색 중 오류 발생: {str(e)}")
            return []

    def _save_state(self):
        """현재 상태를 저장합니다."""
        try:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)
            with open(self.id_map_path, "wb") as f:
                pickle.dump(self.id_to_index, f)
        except Exception as e:
            logger.error(f"상태 저장 중 오류 발생: {str(e)}")
            raise

    def delete_vector(self, id: int) -> bool:
        """
        지정된 ID의 벡터를 삭제합니다.
        
        Args:
            id (int): 삭제할 벡터의 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            if id not in self.id_to_index:
                return False

            # 새로운 인덱스 생성
            new_index = faiss.IndexFlatL2(self.dimension)
            new_metadata = {}
            new_id_map = {}
            next_idx = 0

            # 삭제할 ID를 제외한 모든 벡터 복사
            for vid, idx in self.id_to_index.items():
                if vid != id:
                    vector = self.index.reconstruct(idx).reshape(1, -1)
                    new_index.add(vector)
                    new_metadata[vid] = self.metadata[vid]
                    new_id_map[vid] = next_idx
                    next_idx += 1

            # 새로운 상태로 업데이트
            self.index = new_index
            self.metadata = new_metadata
            self.id_to_index = new_id_map
            self.next_index = next_idx

            # 상태 저장
            self._save_state()
            return True
        except Exception as e:
            logger.error(f"벡터 삭제 중 오류 발생: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """벡터 DB 통계 정보를 반환합니다."""
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_size_bytes": os.path.getsize(self.index_path) if os.path.exists(self.index_path) else 0,
            "metadata_size_bytes": os.path.getsize(self.metadata_path) if os.path.exists(self.metadata_path) else 0,
            "last_modified": datetime.fromtimestamp(os.path.getmtime(self.index_path)).isoformat() 
                            if os.path.exists(self.index_path) else None
        } 