"""
Fallback 전략 서비스

Task 2.8: 에러 핸들링 및 Fallback

LLM 타임아웃이나 에러 발생 시 사용자에게 최소한의 응답을 제공합니다.
"""

import logging
from typing import List
from app.services.vector_search import SearchResult
from app.schemas.search import (
    SearchQueryResponse,
    DocumentSource,
    PerformanceMetrics,
    ResponseMetadata
)

logger = logging.getLogger(__name__)


class FallbackService:
    """Fallback 전략 서비스"""

    @staticmethod
    def create_search_fallback(
        query: str,
        search_results: List[SearchResult],
        error_reason: str,
        performance_data: dict = None
    ) -> SearchQueryResponse:
        """
        검색 결과만 포함된 Fallback 응답 생성

        LLM 타임아웃이나 답변 생성 실패 시 검색 결과만 반환합니다.

        Args:
            query: 검색어
            search_results: 검색 결과 리스트
            error_reason: Fallback 이유 (예: "LLM timeout", "LLM error")
            performance_data: 성능 측정 데이터 (optional)

        Returns:
            SearchQueryResponse: Fallback 응답
        """
        logger.warning(
            f"Fallback 응답 생성: reason={error_reason}, "
            f"query='{query[:50]}...', "
            f"results={len(search_results)}"
        )

        # 검색 결과를 DocumentSource로 변환
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

        # Fallback 답변 메시지
        if search_results:
            fallback_answer = (
                "죄송합니다. 답변 생성에 실패했습니다. "
                "아래 검색 결과를 참고해 주세요."
            )
        else:
            fallback_answer = (
                "죄송합니다. 검색 결과를 찾을 수 없습니다. "
                "다른 검색어로 다시 시도해 주세요."
            )

        # 성능 데이터 구성
        if performance_data:
            performance = PerformanceMetrics(
                embedding_time_ms=performance_data.get("embedding_time_ms", 0),
                search_time_ms=performance_data.get("search_time_ms", 0),
                llm_time_ms=performance_data.get("llm_time_ms", 0),
                total_time_ms=performance_data.get("total_time_ms", 0)
            )
        else:
            performance = PerformanceMetrics(
                embedding_time_ms=0,
                search_time_ms=0,
                llm_time_ms=0,
                total_time_ms=0
            )

        return SearchQueryResponse(
            query=query,
            answer=fallback_answer,
            sources=sources,
            performance=performance,
            metadata=ResponseMetadata(
                is_fallback=True,
                fallback_reason=error_reason,
                model_used="fallback",
                search_result_count=len(search_results)
            )
        )

    @staticmethod
    def create_error_fallback(
        query: str,
        error_message: str
    ) -> SearchQueryResponse:
        """
        에러 발생 시 빈 Fallback 응답 생성

        검색 자체가 실패한 경우 빈 응답을 반환합니다.

        Args:
            query: 검색어
            error_message: 에러 메시지

        Returns:
            SearchQueryResponse: 빈 Fallback 응답
        """
        logger.error(
            f"에러 Fallback 생성: query='{query[:50]}...', "
            f"error={error_message}"
        )

        return SearchQueryResponse(
            query=query,
            answer="검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            sources=[],
            performance=PerformanceMetrics(
                embedding_time_ms=0,
                search_time_ms=0,
                llm_time_ms=0,
                total_time_ms=0
            ),
            metadata=ResponseMetadata(
                is_fallback=True,
                fallback_reason=f"Error: {error_message}",
                model_used="error",
                search_result_count=0
            )
        )

    @staticmethod
    def create_no_results_fallback(
        query: str,
        performance_data: dict = None
    ) -> SearchQueryResponse:
        """
        검색 결과가 없는 경우 Fallback 응답 생성

        Args:
            query: 검색어
            performance_data: 성능 측정 데이터 (optional)

        Returns:
            SearchQueryResponse: 검색 결과 없음 응답
        """
        logger.info(f"검색 결과 없음: query='{query[:50]}...'")

        # 성능 데이터 구성
        if performance_data:
            performance = PerformanceMetrics(
                embedding_time_ms=performance_data.get("embedding_time_ms", 0),
                search_time_ms=performance_data.get("search_time_ms", 0),
                llm_time_ms=0,
                total_time_ms=performance_data.get("total_time_ms", 0)
            )
        else:
            performance = PerformanceMetrics(
                embedding_time_ms=0,
                search_time_ms=0,
                llm_time_ms=0,
                total_time_ms=0
            )

        return SearchQueryResponse(
            query=query,
            answer=(
                "죄송합니다. 해당 검색어에 대한 관련 문서를 찾을 수 없습니다. "
                "다른 검색어로 다시 시도해 주세요."
            ),
            sources=[],
            performance=performance,
            metadata=ResponseMetadata(
                is_fallback=True,
                fallback_reason="No search results",
                model_used="none",
                search_result_count=0
            )
        )
