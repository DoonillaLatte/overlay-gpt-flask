import numpy as np
import faiss
from typing import Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import logging
import os
from db.model import MetadataDB

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self, dimension: int = 768, nlist: int = 100, memory_limit: int = 1000, disk_index_path: str = "vector.index"):
        """
        벡터 데이터베이스를 초기화합니다.

        Args:
            dimension (int): 벡터의 차원 수 (기본값: 768)
            nlist (int): IVF 클러스터 개수 (디스크 인덱스용, 기본값: 100)
            memory_limit: 서버 메모리에 저장할 한계치 인덱스 (기본값: 1000)
            disk_index_path: 저장할 디스크 위치 (기본값: 현재 디렉토리)
        """
        self.dimension = dimension
        self.nlist = nlist
        self.memory_limit = memory_limit
        self.disk_index_path = disk_index_path

        # 메모리 인덱스 (IDMap 사용)
        self.memory_index = faiss.IndexIDMap(faiss.IndexFlatL2(dimension))
        self.memory_ids = []

        # 디스크 인덱스: IVF Flat (근사 검색)
        quantizer = faiss.IndexFlatL2(dimension)
        self.disk_index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)
        self.disk_index_trained = False

        # 디스크 인덱스 로딩 (존재하면)
        if os.path.exists(self.disk_index_path):
            self.disk_index = faiss.read_index(self.disk_index_path)
            self.disk_index_trained = True

        self.model = SentenceTransformer('jhgan/ko-sroberta-multitask')
        self.metadata_db = MetadataDB()

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

    def _flush_memory_to_disk(self):
        """
        메모리가 꽉 찼을 경우 메모리 플러쉬 및 디스크 이동
        """
        if self.memory_index.ntotal == 0:
            return

        logger.info("메모리 플러쉬 및 디스크 이동중")

        vectors = []
        for _id in self.memory_ids:
            vectors.append(self._get_embedding(self.metadata_db.get(_id)["text"]))

        memory_vectors = np.vstack(vectors)
        memory_ids_np = np.array(self.memory_ids).astype('int64')

        if not self.disk_index_trained:
            logger.info("Training disk index...")
            self.disk_index.train(memory_vectors)
            self.disk_index_trained = True

        self.disk_index.add_with_ids(memory_vectors, memory_ids_np)

        # 저장
        faiss.write_index(self.disk_index, self.disk_index_path)

        # 메모리 인덱스 초기화
        self.memory_index.reset()
        self.memory_ids.clear()

    def store_vector(self, id: int, text: str, metadata: Dict[str, Any]) -> None:
        """
        벡터를 저장합니다.

        Args:
            id (int): 벡터 ID
            text (str): 텍스트 데이터
            metadata (Dict[str, Any]): 메타데이터
        """
        vector = self._get_embedding(text)
        self.memory_index.add_with_ids(vector, np.array([id]))
        self.memory_ids.append(id)

        self.metadata_db.save(id, text, metadata)

        if len(self.memory_ids) >= self.memory_limit:
            self._flush_memory_to_disk()

    def get_vector(self, id: int) -> Dict[str, Any]:
        """
        벡터를 조회합니다.

        Args:
            id (int): 벡터 ID

        Returns:
            Dict[str, Any]: 저장된 벡터 데이터
        """
        return self.metadata_db.get(id)

    def delete_vector(self, id: int) -> None:
        """
        벡터를 삭제합니다.

        Args:
            id (int): 벡터 ID
        """
        self.metadata_db.delete(id)

    def search_similar(self, query: str, k: int = 5) -> list:
        """
        유사한 벡터를 검색합니다.

        Args:
            query (str): 검색 쿼리
            k (int): 반환할 결과 수

        Returns:
            list: 유사한 벡터들의 메타데이터 리스트
        """
        # 쿼리 텍스트를를 벡터로 변환
        query_vector = self._get_embedding(query)
        results = []

        # 메모리 유사도 검색
        mem_dist, mem_idx = self.memory_index.search(query_vector, k)
        for i, idx in enumerate(mem_idx[0]):
            if idx != -1:
                item = self.metadata_db.get(idx).copy()
                item['id'] = idx
                item['similarity_score'] = float(1 / (1 + mem_dist[0][i]))
                results.append(item)
                

        # 디스크 유사도 검색
        if self.disk_index_trained:
            disk_dist, disk_idx = self.disk_index.search(query_vector, k)
            for i, idx in enumerate(disk_idx[0]):
                if idx != -1:
                    item = self.metadata_db.get(idx).copy()
                    item['id'] = idx
                    item['similarity_score'] = float(1 / (1 + disk_dist[0][i]))
                    results.append(item)
                    

        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:k]