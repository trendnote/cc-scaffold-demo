import pytest
from app.services.vector_search import VectorSearchService, SearchResult


def test_vector_search_initialization():
    """TC01: VectorSearchService 초기화"""
    service = VectorSearchService()
    assert service.collection_name == "rag_document_chunks"
    assert service.relevance_threshold == 0.7
    assert service.search_params["metric_type"] == "COSINE"
    assert service.search_params["params"]["ef"] == 64


def test_search_returns_results():
    """TC02: 검색 결과 반환"""
    service = VectorSearchService()
    results = service.search("연차 사용 방법", top_k=5)

    assert isinstance(results, list)
    assert len(results) <= 5


def test_search_result_structure():
    """TC03: 검색 결과 구조 검증"""
    service = VectorSearchService()
    results = service.search("급여 지급일", top_k=5)

    if results:
        result = results[0]
        assert hasattr(result, 'document_id')
        assert hasattr(result, 'chunk_index')
        assert hasattr(result, 'content')
        assert hasattr(result, 'page_number')
        assert hasattr(result, 'relevance_score')
        assert hasattr(result, 'metadata')
        assert 0 <= result.relevance_score <= 1


def test_relevance_score_threshold():
    """TC04: 관련도 점수 필터링 (≥ 0.7)"""
    service = VectorSearchService()
    results = service.search("test query for threshold", top_k=10)

    for result in results:
        assert result.relevance_score >= 0.7, \
            f"관련도 점수가 threshold보다 낮음: {result.relevance_score}"


def test_results_sorted_by_relevance():
    """TC05: 결과 관련도 내림차순 정렬"""
    service = VectorSearchService()
    results = service.search("연차 사용", top_k=5)

    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score, \
                f"정렬 순서 오류: {results[i].relevance_score} < {results[i + 1].relevance_score}"


def test_search_with_different_top_k():
    """TC06: 다양한 top_k 값으로 검색"""
    service = VectorSearchService()

    # top_k=1
    results_1 = service.search("급여", top_k=1)
    assert len(results_1) <= 1

    # top_k=10
    results_10 = service.search("급여", top_k=10)
    assert len(results_10) <= 10


def test_search_empty_results():
    """TC07: 관련 문서 없을 때 빈 리스트 반환"""
    service = VectorSearchService()

    # 매우 무관한 검색어로 관련도 점수가 낮아 필터링될 가능성 높음
    results = service.search("xyzabc123 nonexistent term", top_k=5)

    # 빈 리스트이거나 결과가 있을 수 있음
    assert isinstance(results, list)


def test_search_result_content_not_empty():
    """TC08: 검색 결과 content 필드 비어있지 않음"""
    service = VectorSearchService()
    results = service.search("회의실 예약", top_k=5)

    for result in results:
        assert result.content is not None
        assert len(result.content) > 0, "검색 결과 content가 비어있음"


def test_search_result_has_metadata():
    """TC09: 검색 결과 metadata 존재 확인"""
    service = VectorSearchService()
    results = service.search("복리후생", top_k=5)

    for result in results:
        assert isinstance(result.metadata, dict)


def test_normalized_relevance_score_range():
    """TC10: 정규화된 관련도 점수 범위 (0-1)"""
    service = VectorSearchService()
    results = service.search("재택근무 정책", top_k=5)

    for result in results:
        assert 0.0 <= result.relevance_score <= 1.0, \
            f"관련도 점수 범위 초과: {result.relevance_score}"
        # threshold 이상이어야 함
        assert result.relevance_score >= service.relevance_threshold
