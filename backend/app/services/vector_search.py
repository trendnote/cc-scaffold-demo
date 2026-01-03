"""
벡터 검색 서비스

Milvus 벡터 데이터베이스에서 COSINE 유사도 기반 검색을 수행합니다.
권한 기반 필터링을 지원합니다.
"""

from typing import List, Optional
from dataclasses import dataclass
from pymilvus import Collection
import logging

from app.db.milvus_client import get_milvus_collection
from app.services.embedding_service import OllamaEmbeddingService
from app.schemas.user import UserContext
from app.services.access_control import AccessControlService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """벡터 검색 결과"""
    document_id: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    relevance_score: float  # 0-1 정규화된 점수
    metadata: dict


class VectorSearchService:
    """Milvus 벡터 검색 서비스"""

    def __init__(
        self,
        collection_name: str = "rag_document_chunks",
        embedding_service: Optional[OllamaEmbeddingService] = None
    ):
        """
        Args:
            collection_name: Milvus Collection 이름
            embedding_service: 임베딩 서비스 (기본값: OllamaEmbeddingService)
        """
        self.collection_name = collection_name
        self.embedding_service = embedding_service or OllamaEmbeddingService()
        self.collection: Optional[Collection] = None

        # 검색 파라미터
        self.search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64}
        }
        self.relevance_threshold = 0.7  # 최소 관련도 점수

        logger.info(
            f"VectorSearchService 초기화: collection={collection_name}, "
            f"threshold={self.relevance_threshold}"
        )

    def _ensure_collection(self):
        """Collection 로드 (lazy loading)"""
        if self.collection is None:
            self.collection = get_milvus_collection(self.collection_name)
            logger.info(f"Milvus Collection '{self.collection_name}' 로드 완료")

    def search(
        self,
        query: str,
        top_k: int = 5,
        user: Optional[UserContext] = None
    ) -> List[SearchResult]:
        """
        벡터 유사도 검색 실행 (권한 필터링 포함)

        Args:
            query: 검색어
            top_k: 반환할 최대 결과 수
            user: 사용자 컨텍스트 (권한 필터링용)

        Returns:
            List[SearchResult]: 검색 결과 (권한 필터링 및 관련도 정렬 완료)

        Raises:
            ValueError: Collection이 없거나 검색 실패 시
        """
        self._ensure_collection()

        # Step 1: 권한 필터 표현식 생성
        filter_expr = None
        if user:
            filter_expr = AccessControlService.build_filter_expression(user)
            logger.info(
                f"권한 필터 적용: user={user.user_id}, "
                f"filter='{filter_expr}'"
            )

        # Step 2: 쿼리 임베딩 생성
        logger.info(f"검색 시작: query='{query[:50]}...', top_k={top_k}")
        query_embedding = self.embedding_service.embed_query(query)

        # Step 3: Milvus 검색 실행 (필터 포함)
        try:
            search_results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=self.search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=[
                    "document_id",
                    "chunk_index",
                    "content",
                    "page_number",
                    "metadata"
                ]
            )

            # Step 4: 결과 파싱 및 필터링
            results = self._parse_results(search_results[0])

            logger.info(
                f"권한 필터링 검색 완료: found={len(results)}, "
                f"user={user.user_id if user else 'anonymous'}, "
                f"avg_score={sum(r.relevance_score for r in results) / len(results) if results else 0:.3f}"
            )

            return results

        except Exception as e:
            logger.error(f"권한 기반 벡터 검색 실패: {e}")
            raise ValueError(f"벡터 검색 실패: {e}")

    def _parse_results(self, raw_results) -> List[SearchResult]:
        """
        Milvus 검색 결과 파싱 및 필터링

        Args:
            raw_results: Milvus SearchResult 객체

        Returns:
            List[SearchResult]: 파싱된 검색 결과
        """
        results = []

        for hit in raw_results:
            # COSINE 유사도: -1 ~ 1 → 0 ~ 1로 정규화
            normalized_score = (hit.score + 1) / 2

            # 관련도 점수 필터링
            if normalized_score < self.relevance_threshold:
                logger.debug(
                    f"낮은 관련도로 제외: score={normalized_score:.3f}, "
                    f"content='{hit.entity.get('content', '')[:50]}...'"
                )
                continue

            result = SearchResult(
                document_id=hit.entity.get("document_id"),
                chunk_index=hit.entity.get("chunk_index"),
                content=hit.entity.get("content"),
                page_number=hit.entity.get("page_number"),
                relevance_score=normalized_score,
                metadata=hit.entity.get("metadata", {})
            )

            results.append(result)

        # 관련도 내림차순 정렬 (이미 정렬되어 있지만 명시적으로)
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results
