"""
LLM 품질 평가 테스트

Task 2.5a: LLM 기본 답변 생성

NOTE: 이 테스트는 실제 Milvus 데이터와 LLM이 필요합니다.
품질 평가는 수동으로 진행하거나, 충분한 데이터가 있을 때 실행하세요.
"""

import pytest
from app.services.rag_service import RAGService
from app.services.vector_search import SearchResult
from tests.quality.sample_questions import SAMPLE_QUESTIONS


def test_ollama_provider_initialization():
    """TC01: Ollama Provider 초기화 성공"""
    rag_service = RAGService(provider_type="ollama")

    assert rag_service.provider_type == "ollama"
    assert rag_service.llm_provider is not None


@pytest.mark.skip(reason="OpenAI API Key가 필요합니다")
def test_openai_provider_initialization():
    """TC02: OpenAI Provider 초기화 성공"""
    rag_service = RAGService(provider_type="openai")

    assert rag_service.provider_type == "openai"
    assert rag_service.llm_provider is not None


def test_empty_search_results_fallback():
    """TC03: 검색 결과 없을 때 Fallback 메시지 반환"""
    rag_service = RAGService(provider_type="ollama")

    answer = rag_service.generate_answer(
        query="테스트 질문",
        search_results=[]
    )

    assert "관련 문서를 찾을 수 없습니다" in answer


def test_context_building():
    """TC04: 검색 결과로부터 Context 구성 검증"""
    rag_service = RAGService(provider_type="ollama")

    # Mock 검색 결과
    mock_results = [
        SearchResult(
            document_id="doc_001",
            chunk_index=0,
            content="테스트 문서 내용입니다.",
            page_number=1,
            relevance_score=0.95,
            metadata={
                "document_title": "테스트 문서",
                "document_source": "test.pdf"
            }
        )
    ]

    context = rag_service._build_context(mock_results)

    # Context 검증
    assert "테스트 문서" in context
    assert "test.pdf" in context
    assert "테스트 문서 내용입니다" in context
    assert "0.95" in context


@pytest.mark.skip(reason="실제 LLM 호출이 필요하여 시간이 오래 걸립니다")
def test_rag_answer_generation_with_ollama():
    """TC05: Ollama를 사용한 RAG 답변 생성"""
    rag_service = RAGService(provider_type="ollama")

    # Mock 검색 결과
    mock_results = [
        SearchResult(
            document_id="doc_001",
            chunk_index=0,
            content="연차는 입사 1년 후부터 사용 가능하며, 매년 15일이 부여됩니다.",
            page_number=1,
            relevance_score=0.95,
            metadata={
                "document_title": "휴가 규정",
                "document_source": "vacation_policy.pdf"
            }
        )
    ]

    answer = rag_service.generate_answer(
        query="연차 사용 방법은?",
        search_results=mock_results
    )

    # 답변 검증
    assert isinstance(answer, str)
    assert len(answer) > 0
    # 출처 언급 확인 (프롬프트 규칙 3번)
    # Note: LLM이 규칙을 따르지 않을 수 있으므로 엄격하게 검증하지 않음


@pytest.mark.skip(reason="수동 품질 평가용 - 실행 시 비용 발생 가능")
def test_quality_evaluation_sample_questions():
    """TC06: 샘플 5개 질문으로 품질 평가"""
    # 이 테스트는 실제 Milvus 데이터와 함께 수동으로 실행해야 합니다.

    from app.services.vector_search import VectorSearchService

    rag_service = RAGService(provider_type="ollama")
    vector_search = VectorSearchService()

    results = []

    for sample in SAMPLE_QUESTIONS:
        question_id = sample["id"]
        question = sample["question"]

        # 1. 벡터 검색
        search_results = vector_search.search(question, top_k=3)

        # 2. RAG 답변 생성
        answer = rag_service.generate_answer(question, search_results)

        results.append({
            "id": question_id,
            "question": question,
            "answer": answer,
            "search_count": len(search_results)
        })

    # 결과 출력
    for result in results:
        print(f"\n[{result['id']}] {result['question']}")
        print(f"검색 결과: {result['search_count']}건")
        print(f"답변: {result['answer']}")

    # NOTE: 실제 품질 평가는 수동으로 진행
    # 각 답변을 다음 기준으로 평가:
    # - 정확도 (40점): 질문에 정확한 답변 포함
    # - 출처 명시 (30점): 문서 출처 명확히 언급
    # - 유창성 (20점): 자연스러운 한국어
    # - 간결성 (10점): 3-5문장 이내
