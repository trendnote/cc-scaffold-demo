"""
통합 검색 서비스

Task 2.3-2.6에서 점진적으로 완성되는 통합 검색 서비스입니다.
Task 2.3 버전: 벡터 검색만 포함
Task 2.4 버전: 권한 기반 필터링 추가
Task 2.6 버전: 출처 추적 및 응답 구성 (RAG 통합, 성능 측정)
"""

from typing import List, Optional
from app.schemas.search import DocumentSource, SearchQueryResponse
from app.schemas.user import UserContext
from app.services.vector_search import VectorSearchService, SearchResult
from app.services.rag_service import RAGService
from app.services.response_builder import ResponseBuilder
from app.utils.timer import PerformanceTimer
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """통합 검색 서비스 (Task 2.3-2.6에서 점진적 완성)"""

    def __init__(self):
        """SearchService 초기화"""
        self.vector_search = VectorSearchService()
        self.rag_service = RAGService(provider_type="ollama")
        logger.info("SearchService 초기화 완료 (VectorSearch + RAG)")

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

    def search(
        self,
        query: str,
        limit: int = 5,
        user: Optional[UserContext] = None,
        timer: Optional[PerformanceTimer] = None
    ) -> SearchQueryResponse:
        """
        전체 검색 플로우 (Task 2.6 완성: 벡터 검색 + RAG 답변 생성 + 성능 측정)

        Args:
            query: 검색어
            limit: 최대 결과 수
            user: 사용자 컨텍스트 (권한 필터링용)
            timer: 성능 측정 타이머 (없으면 자동 생성)

        Returns:
            SearchQueryResponse: 구조화된 응답 (답변, 출처, 성능 데이터)
        """
        if timer is None:
            timer = PerformanceTimer()

        logger.info(
            f"검색 플로우 시작: query='{query}', limit={limit}, "
            f"user={user.user_id if user else 'anonymous'}"
        )

        # Step 1: 쿼리 임베딩 생성 (성능 측정)
        with timer.measure("embedding"):
            # 임베딩은 vector_search.search 내부에서 수행되지만
            # 여기서는 별도로 측정하지 않고 search_time에 포함
            pass

        # Step 2: 벡터 검색 (성능 측정)
        with timer.measure("search"):
            search_results = self.vector_search.search(
                query,
                top_k=limit,
                user=user
            )

        # Step 3: RAG 답변 생성 (성능 측정)
        with timer.measure("llm"):
            rag_result = self.rag_service.generate_answer_with_fallback(
                query, search_results
            )

        # Step 4: 응답 구성
        response = ResponseBuilder.build_search_response(
            query=query,
            answer=rag_result["answer"],
            search_results=search_results,
            performance={
                "embedding_time_ms": timer.get("embedding"),
                "search_time_ms": timer.get("search"),
                "llm_time_ms": timer.get("llm"),
                "total_time_ms": timer.get_total()
            },
            is_fallback=rag_result["is_fallback"],
            fallback_reason=rag_result["fallback_reason"],
            model_used=f"{self.rag_service.provider_type}/llama3"
        )

        logger.info(
            f"검색 플로우 완료: query_id={response.query_id}, "
            f"total_time={timer.get_total()}ms, sources={len(search_results)}"
        )

        return response
