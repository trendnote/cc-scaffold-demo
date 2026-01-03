"""
RAG 안정성 통합 테스트

Task 2.5b: LLM 안정성 강화

NOTE: 이 테스트는 실제 Milvus 데이터와 LLM이 필요합니다.
End-to-End 테스트로, 전체 플로우를 검증합니다.
"""

import pytest
from app.services.rag_service import RAGService
from app.services.vector_search import VectorSearchService, SearchResult


def test_rag_service_initialization():
    """TC01: RAG Service 초기화 성공"""
    rag_service = RAGService(provider_type="ollama")

    assert rag_service.provider_type == "ollama"
    assert rag_service.llm_provider is not None
    assert rag_service.CONFIDENCE_THRESHOLD == 0.5


def test_fallback_constants_defined():
    """TC02: Fallback 상수 정의 확인"""
    rag_service = RAGService(provider_type="ollama")

    assert rag_service.FALLBACK_NO_DOCUMENTS is not None
    assert rag_service.FALLBACK_LOW_CONFIDENCE is not None
    assert rag_service.FALLBACK_NO_SOURCE is not None


def test_empty_results_fallback():
    """TC03: 빈 검색 결과 → Fallback"""
    rag_service = RAGService(provider_type="ollama")

    answer = rag_service.generate_answer(
        query="빈 결과 테스트",
        search_results=[]
    )

    assert answer == rag_service.FALLBACK_NO_DOCUMENTS


def test_low_confidence_fallback():
    """TC04: 낮은 신뢰도 → Fallback"""
    rag_service = RAGService(provider_type="ollama")

    low_confidence_results = [
        SearchResult(
            document_id="doc_001",
            chunk_index=0,
            content="무관한 내용",
            page_number=1,
            relevance_score=0.2,
            metadata={
                "document_title": "테스트",
                "document_source": "test.pdf"
            }
        )
    ]

    answer = rag_service.generate_answer(
        query="테스트 질문",
        search_results=low_confidence_results
    )

    assert answer == rag_service.FALLBACK_LOW_CONFIDENCE


@pytest.mark.skip(reason="실제 LLM 호출이 필요하여 시간이 오래 걸립니다")
def test_end_to_end_rag_with_vector_search():
    """TC05: End-to-End RAG 플로우 (검색 → 답변 생성)"""
    # 전체 RAG 플로우 테스트
    vector_search = VectorSearchService()
    rag_service = RAGService(provider_type="ollama")

    # Step 1: 벡터 검색
    query = "테스트 질문"
    search_results = vector_search.search(query, top_k=3)

    # Step 2: RAG 답변 생성
    if search_results:
        answer = rag_service.generate_answer(query, search_results)

        # 답변 검증
        assert isinstance(answer, str)
        assert len(answer) > 0


def test_source_citation_patterns():
    """TC06: 다양한 출처 패턴 검증"""
    rag_service = RAGService(provider_type="ollama")

    test_cases = [
        ("휴가 규정 문서에 따르면...", True),
        ("출처: 급여 규정", True),
        ("회의실 예약 규정에 의하면...", True),
        ("[문서 1]에서 발췌", True),
        ("따라서 다음과 같습니다.", True),
        ("그냥 답변입니다.", False),
        ("아무 정보 없음.", False),
    ]

    for answer, expected in test_cases:
        has_source = rag_service._has_source_citation(answer)
        assert has_source == expected, f"Failed for: {answer}"


def test_generate_answer_with_fallback_structure():
    """TC07: Fallback 정보 포함 응답 구조 검증"""
    rag_service = RAGService(provider_type="ollama")

    result = rag_service.generate_answer_with_fallback(
        query="테스트",
        search_results=[]
    )

    # 응답 구조 검증
    assert isinstance(result, dict)
    assert "answer" in result
    assert "is_fallback" in result
    assert "fallback_reason" in result
    assert "search_results" in result

    # Fallback 여부 검증
    assert result["is_fallback"] is True
    assert result["fallback_reason"] == "no_documents"
    assert isinstance(result["search_results"], list)
