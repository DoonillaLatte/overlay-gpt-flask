from typing import Dict, Any, List, Optional, Tuple
import logging
from databases.vector_database import VectorDatabase
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self, storage_dir: str = "vector_db"):
        """
        VectorDBService를 초기화합니다.
        
        Args:
            storage_dir (str): 벡터 데이터베이스 저장 디렉토리 (기본값: "vector_db")
        """
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self._vector_db = VectorDatabase(storage_dir=storage_dir)

    def store_document(self, doc_id: int, content: str, doc_type: str, metadata: Dict[str, Any]) -> bool:
        """
        문서를 벡터 데이터베이스에 저장합니다.
        
        Args:
            doc_id (int): 문서 ID
            content (str): 문서 내용
            doc_type (str): 문서 타입 (예: "ppt", "word")
            metadata (Dict[str, Any]): 추가 메타데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 메타데이터 준비
            full_metadata = {
                "type": doc_type,
                "original_metadata": metadata,
                "stored_at": datetime.now().isoformat()
            }
            
            # 벡터 저장
            return self._vector_db.store_vector(doc_id, content, full_metadata)
        except Exception as e:
            logger.error(f"문서 저장 중 오류 발생: {str(e)}")
            return False

    def find_similar_documents(self, query: str, k: int = 5) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        쿼리와 유사한 문서들을 검색합니다.
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수 (기본값: 5)
            
        Returns:
            List[Tuple[int, float, Dict[str, Any]]]: (문서 ID, 유사도 점수, 메타데이터) 튜플의 리스트
        """
        try:
            return self._vector_db.search_similar(query, k)
        except Exception as e:
            logger.error(f"유사 문서 검색 중 오류 발생: {str(e)}")
            return []

    def delete_document(self, doc_id: int) -> bool:
        """
        문서를 삭제합니다.
        
        Args:
            doc_id (int): 삭제할 문서 ID
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            return self._vector_db.delete_vector(doc_id)
        except Exception as e:
            logger.error(f"문서 삭제 중 오류 발생: {str(e)}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        벡터 데이터베이스 통계를 반환합니다.
        
        Returns:
            Dict[str, Any]: 통계 정보
        """
        try:
            return self._vector_db.get_statistics()
        except Exception as e:
            logger.error(f"통계 조회 중 오류 발생: {str(e)}")
            return {
                "total_vectors": 0,
                "active_vectors": 0,
                "deleted_vectors": 0,
                "index_size": 0,
                "last_optimized": None
            } 