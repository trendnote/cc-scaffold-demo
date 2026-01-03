"""
통합 검색 서비스

Task 2.3-2.6에서 점진적으로 완성되는 통합 검색 서비스입니다.
Task 2.3 버전: 벡터 검색만 포함
Task 2.4 버전: 권한 기반 필터링 추가
"""

from typing import List, Optional
from app.schemas.search import DocumentSource
from app.schemas.user import UserContext
from app.services.vector_search import VectorSearchService, SearchResult
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """통합 검색 서비스 (Task 2.3-2.6에서 점진적 완성)"""

    def __init__(self):
        """SearchService 초기화"""
        self.vector_search = VectorSearchService()
        logger.info("SearchService 초기화 완료")

    def search_documents(
        self,
        query: str,
        limit: int = 5,
        user: Optional[UserContext] = None
    ) -> List[DocumentSource]:
        """
        문서 검색 (Task 2.4 버전: 권한 필터링 포함)

        Args:
            query: 검색어
            limit: 최대 결과 수
            user: 사용자 컨텍스트 (권한 필터링용)

        Returns:
            List[DocumentSource]: 검색된 문서 출처 리스트 (권한 필터링 완료)
        """
        logger.info(
            f"문서 검색 시작: query='{query}', limit={limit}, "
            f"user={user.user_id if user else 'anonymous'}"
        )

        # Step 1: 벡터 검색 (권한 필터링 포함)
        search_results = self.vector_search.search(
            query,
            top_k=limit,
            user=user
        )

        # Step 2: DocumentSource 스키마로 변환
        sources = [
            DocumentSource(
                document_id=result.document_id,
                document_title=result.metadata.get("document_title", "Unknown"),
                document_source=result.metadata.get("document_source", "Unknown"),
                chunk_content=result.content,
                page_number=result.page_number,
                relevance_score=result.relevance_score
            )
            for result in search_results
        ]

        logger.info(
            f"검색 완료: query='{query}', results={len(sources)}, "
            f"user={user.user_id if user else 'anonymous'}"
        )

        return sources
