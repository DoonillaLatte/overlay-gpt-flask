from typing import Dict, Any, List
import logging
from vector_database import VectorDatabase

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self):
        self._vector_db = VectorDatabase()

    def store_program_info(self, program_id: int, program_type: str, program_context: str) -> None:
        """
        프로그램 정보를 벡터 데이터베이스에 저장합니다.
        
        Args:
            program_id (int): 프로그램 ID
            program_type (str): 프로그램 타입 (예: excel, word 등)
            program_context (str): 프로그램 컨텍스트
        """
        try:
            # 프로그램 정보를 벡터로 변환
            program_info = f"{program_type} {program_context}"
            
            # 벡터 데이터베이스에 저장
            self._vector_db.store_vector(
                id=program_id,
                text=program_info,
                metadata={
                    "type": program_type,
                    "context": program_context
                }
            )
            
            logger.info(f"프로그램 정보가 벡터 DB에 저장되었습니다. ID: {program_id}")
            
        except Exception as e:
            logger.error(f"벡터 DB 저장 중 오류 발생: {str(e)}")
            raise

    def get_program_info(self, program_id: int) -> Dict[str, Any]:
        """
        프로그램 정보를 벡터 데이터베이스에서 조회합니다.
        
        Args:
            program_id (int): 프로그램 ID
            
        Returns:
            Dict[str, Any]: 프로그램 정보 (metadata)
        """
        try:
            vector_data = self._vector_db.get_vector(program_id)
            return vector_data.get("metadata", {})
        except Exception as e:
            logger.error(f"벡터 DB 조회 중 오류 발생: {str(e)}")
            raise

    def delete_program_info(self, program_id: int) -> None:
        """
        프로그램 정보를 벡터 데이터베이스에서 삭제합니다.
        
        Args:
            program_id (int): 프로그램 ID
        """
        try:
            self._vector_db.delete_vector(program_id)
            logger.info(f"프로그램 정보가 벡터 DB에서 삭제되었습니다. ID: {program_id}")
        except Exception as e:
            logger.error(f"벡터 DB 삭제 중 오류 발생: {str(e)}")
            raise

    def search_similar_programs(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 프로그램을 검색합니다.
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 유사한 프로그램 정보 리스트
        """
        try:
            results = self._vector_db.search_similar(query, k)
            logger.info(f"유사 프로그램 검색 완료. 쿼리: {query}, 결과 수: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"유사 프로그램 검색 중 오류 발생: {str(e)}")
            raise 