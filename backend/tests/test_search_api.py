import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_search_api_valid_query():
    """TC01: 정상 검색어 → 200 OK"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "연차 사용 방법은 무엇인가요"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "연차 사용 방법은 무엇인가요"
    assert "answer" in data
    assert "sources" in data
    assert "performance" in data
    assert "metadata" in data
    assert isinstance(data["sources"], list)


def test_search_api_short_query():
    """TC02: 짧은 검색어 → 422 Validation Error"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "급여"}  # 2자 (최소 5자 필요)
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_search_api_sql_injection():
    """TC03: SQL Injection 시도 → 422 Validation Error"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "SELECT * FROM users WHERE 1=1"}
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # 에러 메시지에 "허용되지 않는 패턴" 또는 관련 메시지 포함
    error_msg = str(data["detail"])
    assert "허용되지 않는" in error_msg or "패턴" in error_msg


def test_search_api_xss_attack():
    """TC04: XSS 공격 시도 → 422 Validation Error"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "<script>alert('xss')</script>"}
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    # XSS 관련 에러 메시지 확인
    error_msg = str(data["detail"])
    assert "스크립트" in error_msg or "허용되지 않는" in error_msg or "한글, 영어, 숫자" in error_msg
