"""
검색 응답 통합 테스트

Task 2.6: 출처 추적 및 응답 구성
"""

import pytest
from app.schemas.search import (
    SearchQueryResponse,
    DocumentSource,
    PerformanceMetrics,
    ResponseMetadata
)
from app.services.response_builder import ResponseBuilder
from app.services.vector_search import SearchResult
from app.utils.timer import PerformanceTimer


def test_performance_timer():
    """TC01: PerformanceTimer 기본 동작 확인"""
    timer = PerformanceTimer()

    with timer.measure("operation1"):
        import time
        time.sleep(0.01)  # 10ms

    with timer.measure("operation2"):
        time.sleep(0.02)  # 20ms

    # 측정값 검증
    assert timer.get("operation1") >= 10
    assert timer.get("operation2") >= 20
    assert timer.get_total() >= 30

    # 없는 작업은 0 반환
    assert timer.get("nonexistent") == 0


def test_performance_timer_get_all():
    """TC02: PerformanceTimer.get_all() 테스트"""
    timer = PerformanceTimer()

    with timer.measure("test1"):
        pass

    with timer.measure("test2"):
        pass

    all_timings = timer.get_all()
    assert isinstance(all_timings, dict)
    assert "test1" in all_timings
    assert "test2" in all_timings


def test_response_builder_to_document_source():
    """TC03: SearchResult → DocumentSource 변환"""
    search_result = SearchResult(
        document_id="doc_001",
        chunk_index=0,
        content="테스트 문서 내용입니다.",
        page_number=3,
        relevance_score=0.95,
        metadata={
            "document_title": "테스트 문서",
            "document_source": "test.pdf"
        }
    )

    doc_source = ResponseBuilder._to_document_source(search_result)

    assert doc_source.document_id == "doc_001"
    assert doc_source.document_title == "테스트 문서"
    assert doc_source.document_source == "test.pdf"
    assert doc_source.chunk_content == "테스트 문서 내용입니다."
    assert doc_source.page_number == 3
    assert doc_source.relevance_score == 0.95


def test_response_builder_build_search_response():
    """TC04: ResponseBuilder.build_search_response() 전체 플로우"""
    # Mock 검색 결과
    search_results = [
        SearchResult(
            document_id="doc_001",
            chunk_index=0,
            content="테스트 내용 1",
            page_number=1,
            relevance_score=0.9,
            metadata={
                "document_title": "문서 1",
                "document_source": "doc1.pdf"
            }
        ),
        SearchResult(
            document_id="doc_002",
            chunk_index=0,
            content="테스트 내용 2",
            page_number=2,
            relevance_score=0.8,
            metadata={
                "document_title": "문서 2",
                "document_source": "doc2.pdf"
            }
        )
    ]

    performance = {
        "embedding_time_ms": 100,
        "search_time_ms": 350,
        "llm_time_ms": 2000,
        "total_time_ms": 2450
    }

    response = ResponseBuilder.build_search_response(
        query="테스트 질문",
        answer="테스트 답변입니다.",
        search_results=search_results,
        performance=performance,
        is_fallback=False,
        fallback_reason=None,
        model_used="ollama/llama3"
    )

    # 응답 검증
    assert isinstance(response, SearchQueryResponse)
    assert response.query == "테스트 질문"
    assert response.answer == "테스트 답변입니다."
    assert len(response.sources) == 2
    assert response.performance.embedding_time_ms == 100
    assert response.performance.total_time_ms == 2450
    assert response.metadata.is_fallback is False
    assert response.metadata.model_used == "ollama/llama3"
    assert response.metadata.search_result_count == 2


def test_search_query_response_schema_validation():
    """TC05: SearchQueryResponse 스키마 검증"""
    response = SearchQueryResponse(
        query="연차 사용 방법",
        answer="답변입니다.",
        sources=[],
        performance=PerformanceMetrics(
            embedding_time_ms=100,
            search_time_ms=400,
            llm_time_ms=2000,
            total_time_ms=2500
        ),
        metadata=ResponseMetadata(
            is_fallback=False,
            model_used="ollama/llama3",
            search_result_count=0
        )
    )

    # query_id 자동 생성 확인
    assert response.query_id.startswith("qry_")
    assert len(response.query_id) == 16  # "qry_" + 12자

    # JSON 직렬화 테스트
    json_data = response.model_dump_json()
    assert "query_id" in json_data
    assert "query" in json_data
    assert "answer" in json_data
    assert "performance" in json_data
    assert "metadata" in json_data


def test_performance_metrics_validation():
    """TC06: PerformanceMetrics 음수 값 검증"""
    # 음수 값은 허용되지 않음
    with pytest.raises(ValueError):
        PerformanceMetrics(
            embedding_time_ms=-100,
            search_time_ms=400,
            llm_time_ms=2000,
            total_time_ms=2300
        )


def test_document_source_relevance_score_validation():
    """TC07: DocumentSource relevance_score 범위 검증 (0-1)"""
    # 0-1 범위 벗어나면 에러
    with pytest.raises(ValueError):
        DocumentSource(
            document_id="doc_001",
            document_title="테스트",
            document_source="test.pdf",
            chunk_content="내용",
            relevance_score=1.5  # 1보다 큼
        )

    with pytest.raises(ValueError):
        DocumentSource(
            document_id="doc_001",
            document_title="테스트",
            document_source="test.pdf",
            chunk_content="내용",
            relevance_score=-0.1  # 0보다 작음
        )
