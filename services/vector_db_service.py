from typing import Dict, Any, List
import logging
from databases.vector_database import VectorDatabase
import os

logger = logging.getLogger(__name__)

class VectorDBService:
    def __init__(self, storage_dir: str = "vector_db", max_vectors: int = 1000):
        """
        VectorDBService를 초기화합니다.
        
        Args:
            storage_dir (str): 벡터 데이터베이스 저장 디렉토리 (기본값: "vector_db")
            max_vectors (int): 최대 저장 벡터 수 (기본값: 1000)
        """
        self.storage_dir = storage_dir
        # 저장 디렉토리가 없으면 생성
        os.makedirs(storage_dir, exist_ok=True)
        self._vector_db = VectorDatabase(storage_dir=storage_dir, max_vectors=max_vectors)

    def store_program_info(self, file_id: int, file_type: str, context: str, volume_id: int) -> None:
        """
        프로그램 정보를 벡터 데이터베이스에 저장합니다.
        동일한 program_id가 있는 경우 기존 데이터를 삭제하고 새로운 데이터를 저장합니다.
        
        Args:
            file_id (int): 파일 ID
            file_type (str): 파일 타입 (예: excel, word 등)
            context (str): 파일 컨텍스트
            volume_id (int): 볼륨 ID
        """
        try:
            # 동일한 program_id가 있는지 확인하고 있다면 삭제
            try:
                self._vector_db.get_vector(file_id)
                self._vector_db.delete_vector(file_id)
                logger.info(f"기존 파일 정보가 삭제되었습니다. ID: {file_id}")
            except:
                pass  # 기존 데이터가 없는 경우 무시
            
            # 프로그램 정보를 벡터로 변환
            program_info = f"{file_type} {context}"
            
            # 벡터 데이터베이스에 저장
            self._vector_db.store_vector(
                id=file_id,  
                text=program_info,
                metadata={
                    "type": file_type,
                    "context": context,
                    "fileId": file_id,
                    "volumeId": volume_id
                }
            )
            
            logger.info(f"프로그램 정보가 벡터 DB에 저장되었습니다. ID: {file_id}")
            
        except Exception as e:
            logger.error(f"벡터 DB 저장 중 오류 발생: {str(e)}")
            raise

    def get_program_info(self, file_id: int) -> Dict[str, Any]:
        """
        프로그램 정보를 벡터 데이터베이스에서 조회합니다.
        
        Args:
            program_id (int): 프로그램 ID
            
        Returns:
            Dict[str, Any]: 프로그램 정보 (metadata)
        """
        try:
            vector_data = self._vector_db.get_vector(file_id)
            return vector_data.get("metadata", {})
        except Exception as e:
            logger.error(f"벡터 DB 조회 중 오류 발생: {str(e)}")
            raise

    def delete_program_info(self, file_id: int) -> None:
        """
        파일 정보를 벡터 데이터베이스에서 삭제합니다.
        
        Args:
            file_id (int): 파일 ID
        """
        try:
            self._vector_db.delete_vector(file_id)
            logger.info(f"파일 정보가 벡터 DB에서 삭제되었습니다. ID: {file_id}")
        except Exception as e:
            logger.error(f"벡터 DB 삭제 중 오류 발생: {str(e)}")
            raise

    def search_similar_programs(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 파일을 검색합니다.
        
        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 유사한 파일 정보 리스트
        """
        try:
            results = self._vector_db.search_similar(query, k)
            logger.info(f"유사 파일 검색 완료. 쿼리: {query}, 결과 수: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"유사 파일 검색 중 오류 발생: {str(e)}")
            raise 