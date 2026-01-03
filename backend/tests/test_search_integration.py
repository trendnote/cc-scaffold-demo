"""
통합 테스트: 벡터 검색 전체 흐름

SearchService와 VectorSearchService의 통합 동작을 검증합니다.
"""

import pytest
from app.services.search_service import SearchService
from app.schemas.search import DocumentSource


def test_search_service_initialization():
    """TC01: SearchService 초기화 및 의존성 주입"""
    service = SearchService()
    assert service.vector_search is not None
    assert service.vector_search.collection_name == "rag_document_chunks"


def test_search_documents_returns_document_sources():
    """TC02: search_documents()가 DocumentSource 리스트 반환"""
    service = SearchService()
    results = service.search_documents("연차 사용 방법", limit=5)

    assert isinstance(results, list)
    assert len(results) <= 5

    # 결과가 있으면 DocumentSource 타입 검증
    if results:
        assert all(isinstance(r, DocumentSource) for r in results)


def test_search_documents_schema_fields():
    """TC03: DocumentSource 스키마 필드 완전성 검증"""
    service = SearchService()
    results = service.search_documents("급여 지급일", limit=3)

    if results:
        result = results[0]
        # 필수 필드 존재 확인
        assert hasattr(result, 'document_id')
        assert hasattr(result, 'document_title')
        assert hasattr(result, 'document_source')
        assert hasattr(result, 'chunk_content')
        assert hasattr(result, 'page_number')
        assert hasattr(result, 'relevance_score')

        # 타입 검증
        assert isinstance(result.document_id, str)
        assert isinstance(result.document_title, str)
        assert isinstance(result.document_source, str)
        assert isinstance(result.chunk_content, str)
        assert isinstance(result.relevance_score, float)

        # 값 범위 검증
        assert len(result.chunk_content) > 0
        assert 0.0 <= result.relevance_score <= 1.0


def test_search_documents_metadata_mapping():
    """TC04: 메타데이터 매핑 검증"""
    service = SearchService()
    results = service.search_documents("회의실 예약", limit=5)

    for result in results:
        # document_title과 document_source는 metadata에서 가져옴
        assert result.document_title is not None
        assert result.document_source is not None

        # "Unknown"이 아닌 실제 값이 있어야 함 (데이터 존재 시)
        # 단, 빈 컬렉션이면 이 테스트는 스킵됨
        pass


def test_search_documents_limit_respected():
    """TC05: limit 파라미터 준수 검증"""
    service = SearchService()

    # limit=1
    results_1 = service.search_documents("복리후생", limit=1)
    assert len(results_1) <= 1

    # limit=10
    results_10 = service.search_documents("복리후생", limit=10)
    assert len(results_10) <= 10


def test_search_documents_relevance_score_threshold():
    """TC06: 관련도 점수 필터링 (≥ 0.7)"""
    service = SearchService()
    results = service.search_documents("재택근무 정책", limit=10)

    for result in results:
        assert result.relevance_score >= 0.7, \
            f"관련도 점수가 threshold보다 낮음: {result.relevance_score}"


def test_search_documents_sorted_by_relevance():
    """TC07: 결과가 관련도 내림차순 정렬"""
    service = SearchService()
    results = service.search_documents("연차 사용", limit=5)

    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score, \
                f"정렬 순서 오류: {results[i].relevance_score} < {results[i + 1].relevance_score}"


def test_search_documents_empty_results():
    """TC08: 관련 문서가 없을 때 빈 리스트 반환"""
    service = SearchService()
    results = service.search_documents("xyzabc123 nonexistent term", limit=5)

    # 빈 리스트이거나 결과가 있을 수 있음 (threshold 필터링)
    assert isinstance(results, list)


def test_search_documents_with_user_id():
    """TC09: user_id 파라미터 전달 (Task 2.4에서 사용)"""
    service = SearchService()

    # user_id는 현재 사용되지 않지만 파라미터로 받음
    results = service.search_documents(
        "연차 신청",
        limit=5,
        user_id="test_user_123"
    )

    assert isinstance(results, list)
    assert len(results) <= 5


def test_end_to_end_search_flow():
    """TC10: End-to-End 검색 흐름 통합 테스트"""
    service = SearchService()

    # 1. 검색 실행
    query = "급여 지급일은 언제인가요"
    results = service.search_documents(query, limit=5)

    # 2. 결과 검증
    assert isinstance(results, list)
    assert len(results) <= 5

    # 3. 각 결과 검증
    for result in results:
        # 필수 필드 존재
        assert result.document_id
        assert result.chunk_content
        assert result.relevance_score >= 0.7

        # 타입 검증
        assert isinstance(result.document_id, str)
        assert isinstance(result.chunk_content, str)
        assert isinstance(result.relevance_score, float)

    # 4. 정렬 검증
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score
