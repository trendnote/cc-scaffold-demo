"""
검색 히스토리 통합 테스트

Task 2.7: 검색 쿼리/응답 저장 및 히스토리 조회
"""

import pytest
from uuid import UUID
from app.repositories.search_repository import SearchRepository
from app.schemas.search import (
    SearchQueryResponse,
    DocumentSource,
    PerformanceMetrics,
    ResponseMetadata
)
from app.models.search import SearchQuery, SearchResponse
from app.models.user import User


@pytest.mark.asyncio
async def test_save_query(db_session):
    """TC01: 검색 쿼리 저장"""
    # 테스트용 사용자 생성
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="test@example.com",
        name="Test User",
        department="IT",
        access_level=2,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    repository = SearchRepository(db_session)

    query_id = await repository.save_query(
        user_id=user.id,
        query="연차 사용 방법은?",
        session_id="session_001"
    )

    assert query_id is not None
    assert isinstance(query_id, UUID)

    # DB에서 조회하여 확인
    from sqlalchemy import select
    stmt = select(SearchQuery).where(SearchQuery.id == query_id)
    result = await db_session.execute(stmt)
    saved_query = result.scalar_one()

    assert saved_query.query == "연차 사용 방법은?"
    assert saved_query.user_id == user.id
    assert saved_query.session_id == "session_001"


@pytest.mark.asyncio
async def test_save_response(db_session):
    """TC02: 검색 응답 저장"""
    # 테스트용 사용자 및 쿼리 생성
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000002"),
        email="test2@example.com",
        name="Test User 2",
        department="IT",
        access_level=2,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    repository = SearchRepository(db_session)
    query_id = await repository.save_query(
        user_id=user.id,
        query="테스트 질문"
    )

    # SearchQueryResponse 생성
    response = SearchQueryResponse(
        query="테스트 질문",
        answer="테스트 답변입니다.",
        sources=[
            DocumentSource(
                document_id="doc_001",
                document_title="문서 1",
                document_source="test.pdf",
                chunk_content="내용",
                relevance_score=0.95
            )
        ],
        performance=PerformanceMetrics(
            embedding_time_ms=100,
            search_time_ms=300,
            llm_time_ms=2000,
            total_time_ms=2400
        ),
        metadata=ResponseMetadata(
            is_fallback=False,
            model_used="ollama/llama3",
            search_result_count=1
        )
    )

    # 응답 저장
    await repository.save_response(query_id, response)

    # DB에서 조회하여 확인
    from sqlalchemy import select
    stmt = select(SearchResponse).where(SearchResponse.query_id == query_id)
    result = await db_session.execute(stmt)
    saved_response = result.scalar_one()

    assert saved_response.answer == "테스트 답변입니다."
    assert len(saved_response.sources) == 1
    assert saved_response.performance["total_time_ms"] == 2400
    assert saved_response.response_metadata["model_used"] == "ollama/llama3"


@pytest.mark.asyncio
async def test_get_user_history_empty(db_session):
    """TC03: 히스토리 조회 (빈 결과)"""
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000003"),
        email="test3@example.com",
        name="Test User 3",
        department="IT",
        access_level=2,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    repository = SearchRepository(db_session)
    result = await repository.get_user_history(
        user_id=user.id,
        page=1,
        page_size=10
    )

    assert result["total"] == 0
    assert result["items"] == []
    assert result["page"] == 1
    assert result["total_pages"] == 0


@pytest.mark.asyncio
async def test_get_user_history_pagination(db_session):
    """TC04: 히스토리 페이지네이션"""
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000004"),
        email="test4@example.com",
        name="Test User 4",
        department="IT",
        access_level=2,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    repository = SearchRepository(db_session)

    # 5개의 검색 쿼리 생성
    for i in range(5):
        await repository.save_query(
            user_id=user.id,
            query=f"테스트 질문 {i+1}"
        )

    # 페이지 1 조회 (page_size=3)
    result = await repository.get_user_history(
        user_id=user.id,
        page=1,
        page_size=3
    )

    assert result["total"] == 5
    assert len(result["items"]) == 3
    assert result["page"] == 1
    assert result["page_size"] == 3
    assert result["total_pages"] == 2

    # 페이지 2 조회
    result_page2 = await repository.get_user_history(
        user_id=user.id,
        page=2,
        page_size=3
    )

    assert len(result_page2["items"]) == 2
    assert result_page2["page"] == 2


@pytest.mark.asyncio
async def test_full_search_history_flow(db_session):
    """TC05: 전체 플로우 테스트 (쿼리 저장 → 응답 저장 → 히스토리 조회)"""
    user = User(
        id=UUID("00000000-0000-0000-0000-000000000005"),
        email="test5@example.com",
        name="Test User 5",
        department="IT",
        access_level=2,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    repository = SearchRepository(db_session)

    # Step 1: 쿼리 저장
    query_id = await repository.save_query(
        user_id=user.id,
        query="전체 플로우 테스트",
        session_id="session_flow"
    )

    # Step 2: 응답 저장
    response = SearchQueryResponse(
        query="전체 플로우 테스트",
        answer="플로우 테스트 답변",
        sources=[],
        performance=PerformanceMetrics(
            embedding_time_ms=50,
            search_time_ms=200,
            llm_time_ms=1500,
            total_time_ms=1750
        ),
        metadata=ResponseMetadata(
            is_fallback=False,
            model_used="ollama/llama3",
            search_result_count=0
        )
    )

    await repository.save_response(query_id, response)

    # Step 3: 히스토리 조회
    history = await repository.get_user_history(
        user_id=user.id,
        page=1,
        page_size=10
    )

    assert history["total"] == 1
    assert len(history["items"]) == 1

    item = history["items"][0]
    assert item["query"] == "전체 플로우 테스트"
    assert item["answer"] == "플로우 테스트 답변"
    assert item["sources_count"] == 0
    assert item["response_time_ms"] == 1750
    assert "created_at" in item
