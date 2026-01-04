"""
에러 핸들링 테스트

Task 2.8: 에러 핸들링 및 Fallback
"""

import pytest
from app.middleware.error_handler import sanitize_error_message
from app.services.fallback_service import FallbackService
from app.services.vector_search import SearchResult
from app.schemas.search import SearchQueryResponse


def test_sanitize_file_path():
    """TC01: 파일 경로 마스킹"""
    message = "Error at /home/user/app/main.py line 123"
    sanitized = sanitize_error_message(message)

    assert "/home/user/app/main.py" not in sanitized
    assert "[path]" in sanitized


def test_sanitize_db_connection():
    """TC02: DB 연결 문자열 마스킹"""
    message = "Connection failed: postgresql://user:pass@localhost:5432/db"
    sanitized = sanitize_error_message(message)

    # 민감 정보가 제거되었는지 확인
    assert "user:pass" not in sanitized
    assert "[hidden]" in sanitized or "[path]" in sanitized


def test_sanitize_ip_address():
    """TC03: IP 주소 마스킹"""
    message = "Connection to 192.168.1.100 failed"
    sanitized = sanitize_error_message(message)

    assert "192.168.1.100" not in sanitized
    assert "[ip]" in sanitized


def test_sanitize_api_key():
    """TC04: API 키 마스킹"""
    message = "API error with api_key=sk-1234567890abcdef"
    sanitized = sanitize_error_message(message)

    assert "sk-1234567890abcdef" not in sanitized
    assert "api_key=[hidden]" in sanitized


def test_sanitize_password():
    """TC05: 비밀번호 마스킹"""
    message = "Authentication failed with password=secretpass123"
    sanitized = sanitize_error_message(message)

    assert "secretpass123" not in sanitized
    assert "password=[hidden]" in sanitized


def test_fallback_with_search_results():
    """TC06: 검색 결과가 있는 Fallback 응답"""
    search_results = [
        SearchResult(
            document_id="doc_001",
            chunk_index=0,
            content="테스트 문서 내용",
            page_number=1,
            relevance_score=0.9,
            metadata={
                "document_title": "테스트 문서",
                "document_source": "test.pdf"
            }
        )
    ]

    response = FallbackService.create_search_fallback(
        query="테스트 질문",
        search_results=search_results,
        error_reason="LLM timeout"
    )

    assert isinstance(response, SearchQueryResponse)
    assert response.metadata.is_fallback is True
    assert response.metadata.fallback_reason == "LLM timeout"
    assert len(response.sources) == 1
    assert "답변 생성에 실패" in response.answer


def test_fallback_without_search_results():
    """TC07: 검색 결과가 없는 Fallback 응답"""
    response = FallbackService.create_search_fallback(
        query="테스트 질문",
        search_results=[],
        error_reason="No results"
    )

    assert isinstance(response, SearchQueryResponse)
    assert response.metadata.is_fallback is True
    assert len(response.sources) == 0
    assert "검색 결과를 찾을 수 없습니다" in response.answer


def test_error_fallback():
    """TC08: 에러 Fallback 응답"""
    response = FallbackService.create_error_fallback(
        query="테스트 질문",
        error_message="Database connection failed"
    )

    assert isinstance(response, SearchQueryResponse)
    assert response.metadata.is_fallback is True
    assert "Error: Database connection failed" in response.metadata.fallback_reason
    assert response.metadata.model_used == "error"
    assert "오류가 발생했습니다" in response.answer


def test_no_results_fallback():
    """TC09: 검색 결과 없음 Fallback 응답"""
    response = FallbackService.create_no_results_fallback(
        query="존재하지 않는 검색어"
    )

    assert isinstance(response, SearchQueryResponse)
    assert response.metadata.is_fallback is True
    assert response.metadata.fallback_reason == "No search results"
    assert len(response.sources) == 0
    assert "관련 문서를 찾을 수 없습니다" in response.answer


def test_fallback_with_performance_data():
    """TC10: 성능 데이터 포함 Fallback 응답"""
    performance_data = {
        "embedding_time_ms": 100,
        "search_time_ms": 300,
        "llm_time_ms": 0,
        "total_time_ms": 400
    }

    response = FallbackService.create_search_fallback(
        query="테스트 질문",
        search_results=[],
        error_reason="LLM error",
        performance_data=performance_data
    )

    assert response.performance.embedding_time_ms == 100
    assert response.performance.search_time_ms == 300
    assert response.performance.llm_time_ms == 0
    assert response.performance.total_time_ms == 400


def test_sanitize_multiple_patterns():
    """TC11: 여러 패턴 동시 마스킹"""
    message = (
        "Error at /app/main.py: "
        "Connection to postgresql://admin:secret@192.168.1.1:5432/db failed. "
        "API_KEY=abc123xyz"
    )
    sanitized = sanitize_error_message(message)

    # 모든 민감 정보가 마스킹되었는지 확인
    assert "/app/main.py" not in sanitized
    assert "admin:secret" not in sanitized
    assert "192.168.1.1" not in sanitized
    assert "abc123xyz" not in sanitized

    # 마스킹된 값들이 포함되었는지 확인
    assert "[path]" in sanitized or "[hidden]" in sanitized
    assert "API_KEY=[hidden]" in sanitized

    # 원본 메시지의 민감 정보가 모두 제거되었는지 재확인
    assert "secret" not in sanitized
    assert "abc123xyz" not in sanitized


def test_error_response_schema_validation():
    """TC12: ErrorResponse 스키마 검증"""
    from app.schemas.errors import ErrorResponse, ErrorDetail

    # 정상적인 에러 응답 생성
    error_response = ErrorResponse(
        error="ValidationError",
        message="검증 실패",
        details=[
            ErrorDetail(
                field="query",
                message="5자 이상이어야 합니다",
                code="string_too_short"
            )
        ],
        request_id="req_123"
    )

    # JSON 직렬화 테스트
    json_data = error_response.model_dump()
    assert json_data["error"] == "ValidationError"
    assert json_data["message"] == "검증 실패"
    assert len(json_data["details"]) == 1
    assert json_data["request_id"] == "req_123"
    assert "timestamp" in json_data
