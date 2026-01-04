"""
API 응답 구성 서비스

Task 2.6: 출처 추적 및 응답 구성
"""

from typing import List, Optional, Dict, Any
from app.schemas.search import (
    SearchQueryResponse,
    DocumentSource,
    PerformanceMetrics,
    ResponseMetadata
)
from app.services.vector_search import SearchResult
import logging

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """API 응답 구성 서비스"""

    @staticmethod
    def build_search_response(
        query: str,
        answer: str,
        search_results: List[SearchResult],
        performance: Dict[str, int],
        is_fallback: bool = False,
        fallback_reason: Optional[str] = None,
        model_used: str = "ollama/llama3"
    ) -> SearchQueryResponse:
        """
        구조화된 검색 응답 생성

        Args:
            query: 검색어
            answer: 생성된 답변
            search_results: 검색 결과 리스트
            performance: 성능 측정 데이터 dict
                - embedding_time_ms: 임베딩 생성 시간
                - search_time_ms: 벡터 검색 시간
                - llm_time_ms: LLM 답변 생성 시간
                - total_time_ms: 전체 처리 시간
            is_fallback: Fallback 여부
            fallback_reason: Fallback 이유
            model_used: 사용된 LLM 모델

        Returns:
            SearchQueryResponse: 구조화된 응답
        """
        logger.info(
            f"응답 구성 시작: query='{query[:30]}...', "
            f"sources={len(search_results)}, "
            f"is_fallback={is_fallback}"
        )

        # Step 1: DocumentSource 변환
        sources = [
            ResponseBuilder._to_document_source(result)
            for result in search_results
        ]

        # Step 2: PerformanceMetrics 생성
        perf_metrics = PerformanceMetrics(
            embedding_time_ms=performance.get("embedding_time_ms", 0),
            search_time_ms=performance.get("search_time_ms", 0),
            llm_time_ms=performance.get("llm_time_ms", 0),
            total_time_ms=performance.get("total_time_ms", 0)
        )

        # Step 3: ResponseMetadata 생성
        metadata = ResponseMetadata(
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            model_used=model_used,
            search_result_count=len(search_results)
        )

        # Step 4: SearchQueryResponse 생성
        response = SearchQueryResponse(
            query=query,
            answer=answer,
            sources=sources,
            performance=perf_metrics,
            metadata=metadata
        )

        logger.info(
            f"응답 구성 완료: query_id={response.query_id}, "
            f"total_time={perf_metrics.total_time_ms}ms, "
            f"sources={len(sources)}"
        )

        return response

    @staticmethod
    def _to_document_source(result: SearchResult) -> DocumentSource:
        """
        SearchResult → DocumentSource 변환

        Args:
            result: 검색 결과

        Returns:
            DocumentSource: 문서 출처 정보
        """
        return DocumentSource(
            document_id=result.document_id,
            document_title=result.metadata.get("document_title", "Unknown"),
            document_source=result.metadata.get("document_source", "Unknown"),
            chunk_content=result.content,
            page_number=result.page_number,
            relevance_score=result.relevance_score
        )
