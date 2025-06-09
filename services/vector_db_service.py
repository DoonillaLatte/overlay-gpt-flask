from typing import Dict, Any, List
import logging
from databases.vector_database import VectorDatabase
import os
import json

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
        
        # 파일 타입별 VectorDB 초기화
        self._vector_dbs = {
            'excel': VectorDatabase(storage_dir=os.path.join(storage_dir, "excel_db"), max_vectors=max_vectors),
            'word': VectorDatabase(storage_dir=os.path.join(storage_dir, "word_db"), max_vectors=max_vectors),
            'hwp': VectorDatabase(storage_dir=os.path.join(storage_dir, "hwp_db"), max_vectors=max_vectors),
            'powerpoint': VectorDatabase(storage_dir=os.path.join(storage_dir, "powerpoint_db"), max_vectors=max_vectors)
        }
        logger.debug(f"VectorDBService 초기화 완료. 저장 디렉토리: {storage_dir}, 최대 벡터 수: {max_vectors}")

    def _get_db_by_type(self, file_type: str) -> VectorDatabase:
        """
        파일 타입에 해당하는 VectorDB를 반환합니다.
        
        Args:
            file_type (str): 파일 타입 (excel, word, hwp, powerpoint)
            
        Returns:
            VectorDatabase: 해당 파일 타입의 VectorDB
        """
        normalized_type = file_type.lower()
        
        # text 타입은 지원하지 않음을 명시적으로 처리
        if normalized_type == 'text':
            raise ValueError(f"Text 파일 타입은 벡터 DB를 지원하지 않습니다: {file_type}")
            
        if normalized_type not in self._vector_dbs:
            raise ValueError(f"지원하지 않는 파일 타입입니다: {file_type}")
        return self._vector_dbs[normalized_type]

    def store_program_info(self, file_id: int, file_type: str, context: str, volume_id: int) -> None:
        """
        프로그램 정보를 벡터 데이터베이스에 저장합니다.
        동일한 file_id가 있는 경우 기존 데이터를 삭제하고 새로운 데이터를 저장합니다.
        
        Args:
            file_id (int): 파일 ID
            file_type (str): 파일 타입 (excel, word, hwp, powerpoint)
            context (str): 파일 컨텍스트
            volume_id (int): 볼륨 ID
        """
        try:
            # text 타입은 벡터 DB에 저장하지 않음
            if file_type.lower() == 'text':
                logger.info(f"Text 타입은 벡터 DB에 저장하지 않습니다 - FileID: {file_id}, FileType: {file_type}")
                return
                
            vector_db = self._get_db_by_type(file_type)
            
            # 동일한 file_id가 있는지 확인하고 있다면 삭제
            try:
                existing_data = vector_db.get_vector(file_id)
                vector_db.delete_vector(file_id)
                logger.info(f"기존 파일 정보가 삭제되었습니다. Type: {file_type}, ID: {file_id}")
                logger.debug(f"삭제된 기존 데이터: {json.dumps(existing_data, ensure_ascii=False)}")
            except:
                pass  # 기존 데이터가 없는 경우 무시
            
            # 프로그램 정보를 벡터로 변환
            program_info = f"{file_type} {context}"
            
            # 벡터 데이터베이스에 저장
            vector_db.store_vector(
                id=file_id,  
                text=program_info,
                metadata={
                    "type": file_type,
                    "context": context,
                    "fileId": file_id,
                    "volumeId": volume_id
                }
            )
            
            logger.info(f"파일 정보가 벡터 DB에 저장되었습니다. Type: {file_type}, ID: {file_id}")
            logger.debug(f"저장된 데이터: {json.dumps({'text': program_info, 'metadata': {'type': file_type, 'context': context, 'fileId': file_id, 'volumeId': volume_id}}, ensure_ascii=False)}")
            
        except Exception as e:
            logger.error(f"벡터 DB 저장 중 오류 발생: {str(e)}")
            raise

    def get_program_info(self, file_id: int, file_type: str) -> Dict[str, Any]:
        """
        프로그램 정보를 벡터 데이터베이스에서 조회합니다.
        
        Args:
            file_id (int): 파일 ID
            file_type (str): 파일 타입 (excel, word, hwp, powerpoint)
            
        Returns:
            Dict[str, Any]: 프로그램 정보 (metadata)
        """
        try:
            # text 타입은 벡터 DB에서 조회하지 않음
            if file_type.lower() == 'text':
                logger.info(f"Text 타입은 벡터 DB에서 조회하지 않습니다 - FileID: {file_id}, FileType: {file_type}")
                return {}
                
            vector_db = self._get_db_by_type(file_type)
            vector_data = vector_db.get_vector(file_id)
            return vector_data.get("metadata", {})
        except Exception as e:
            logger.error(f"벡터 DB 조회 중 오류 발생: {str(e)}")
            raise

    def delete_program_info(self, file_id: int, file_type: str) -> None:
        """
        파일 정보를 벡터 데이터베이스에서 삭제합니다.
        
        Args:
            file_id (int): 파일 ID
            file_type (str): 파일 타입 (excel, word, hwp, powerpoint)
        """
        try:
            # text 타입은 벡터 DB에서 삭제하지 않음
            if file_type.lower() == 'text':
                logger.info(f"Text 타입은 벡터 DB에서 삭제하지 않습니다 - FileID: {file_id}, FileType: {file_type}")
                return
                
            vector_db = self._get_db_by_type(file_type)
            vector_db.delete_vector(file_id)
            logger.info(f"파일 정보가 벡터 DB에서 삭제되었습니다. Type: {file_type}, ID: {file_id}")
        except Exception as e:
            logger.error(f"벡터 DB 삭제 중 오류 발생: {str(e)}")
            raise

    def search_similar_programs(self, query: str, file_type: str = None, k: int = 5) -> List[Dict[str, Any]]:
        """
        유사한 파일을 검색합니다.
        
        Args:
            query (str): 검색 쿼리
            file_type (str, optional): 특정 파일 타입만 검색할 경우 지정
            k (int): 반환할 결과 수
            
        Returns:
            List[Dict[str, Any]]: 유사한 파일 정보 리스트
        """
        try:
            logger.debug(f"유사 파일 검색 시작. 쿼리: {query}, 파일 타입: {file_type}, k: {k}")
            
            # text 타입은 유사도 검색을 하지 않음
            if file_type and file_type.lower() == 'text':
                logger.info(f"Text 타입은 유사도 검색을 하지 않습니다 - FileType: {file_type}")
                return []
            
            if file_type:
                # 특정 파일 타입에서만 검색
                vector_db = self._get_db_by_type(file_type)
                results = vector_db.search_similar(query, k)
                logger.debug(f"특정 파일 타입({file_type}) 검색 결과: {json.dumps(results, ensure_ascii=False)}")
            else:
                # 모든 파일 타입에서 검색
                all_results = []
                for db_type, vector_db in self._vector_dbs.items():
                    results = vector_db.search_similar(query, k)
                    logger.debug(f"파일 타입 {db_type} 검색 결과: {json.dumps(results, ensure_ascii=False)}")
                    all_results.extend(results)
                
                # 유사도 점수로 정렬하고 상위 k개 선택
                results = sorted(all_results, key=lambda x: x['similarity_score'], reverse=True)[:k]
                logger.debug(f"전체 검색 결과 (상위 {k}개): {json.dumps(results, ensure_ascii=False)}")
            
            logger.info(f"유사 파일 검색 완료. 파일 타입: {file_type if file_type else '전체'}, 쿼리: {query}, 결과 수: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"유사 파일 검색 중 오류 발생: {str(e)}")
            raise 