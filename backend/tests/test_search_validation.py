import pytest
from pydantic import ValidationError
from app.schemas.search import SearchQueryRequest


# ============================================================================
# Happy Path Tests (4개)
# ============================================================================

def test_valid_korean_query():
    """TC01: 유효한 한글 검색어"""
    request = SearchQueryRequest(query="연차 사용 방법은 무엇인가요")
    assert request.query == "연차 사용 방법은 무엇인가요"
    assert request.limit == 5  # default


def test_valid_english_query():
    """TC02: 유효한 영어 검색어"""
    request = SearchQueryRequest(query="How to use vacation days")
    assert request.query == "How to use vacation days"


def test_valid_mixed_query():
    """TC03: 한글+영어+숫자 혼합"""
    request = SearchQueryRequest(query="2024년 HR 정책 변경사항")
    assert request.query == "2024년 HR 정책 변경사항"


def test_valid_query_with_punctuation():
    """TC04: 허용된 특수문자 (?, ., !, -, 괄호)"""
    request = SearchQueryRequest(query="급여일은 언제인가요? (월급)")
    assert request.query == "급여일은 언제인가요? (월급)"


# ============================================================================
# Edge Cases (4개)
# ============================================================================

def test_minimum_length_query():
    """TC05: 최소 길이 (5자)"""
    request = SearchQueryRequest(query="급여일은요")
    assert request.query == "급여일은요"
    assert len(request.query) == 5  # 5자 정확히


def test_maximum_length_query():
    """TC06: 최대 길이 (200자)"""
    long_query = "가" * 200
    request = SearchQueryRequest(query=long_query)
    assert len(request.query) == 200


def test_whitespace_normalization():
    """TC07: 공백 정규화 (여러 공백 → 하나)"""
    request = SearchQueryRequest(query="연차    사용    방법")
    assert request.query == "연차 사용 방법"


def test_limit_parameter_range():
    """TC08: limit 파라미터 범위 (1-20)"""
    request = SearchQueryRequest(query="테스트 검색어입니다", limit=10)
    assert request.limit == 10

    request_min = SearchQueryRequest(query="테스트 검색어입니다", limit=1)
    assert request_min.limit == 1

    request_max = SearchQueryRequest(query="테스트 검색어입니다", limit=20)
    assert request_max.limit == 20


# ============================================================================
# Error Handling (6개)
# ============================================================================

def test_too_short_query():
    """TC09: 너무 짧은 검색어 (4자 이하)"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="급여")

    errors = exc_info.value.errors()
    assert any("at least 5 characters" in str(error) for error in errors)


def test_too_long_query():
    """TC10: 너무 긴 검색어 (201자 이상)"""
    long_query = "가" * 201
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query=long_query)

    errors = exc_info.value.errors()
    assert any("at most 200 characters" in str(error) for error in errors)


def test_empty_string():
    """TC11: 빈 문자열"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="")

    errors = exc_info.value.errors()
    assert any(error["type"] == "string_too_short" for error in errors)


def test_whitespace_only_query():
    """TC12: 공백만 있는 검색어"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="     ")

    errors = exc_info.value.errors()
    # 공백만 있으면 정규화 후 빈 값이 되어 validator에서 거부됨
    assert len(errors) > 0


def test_limit_below_range():
    """TC13: limit 범위 미만 (0)"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="테스트 검색어입니다", limit=0)

    errors = exc_info.value.errors()
    assert any("greater than or equal to 1" in str(error) for error in errors)


def test_limit_above_range():
    """TC14: limit 범위 초과 (21)"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="테스트 검색어입니다", limit=21)

    errors = exc_info.value.errors()
    assert any("less than or equal to 20" in str(error) for error in errors)


# ============================================================================
# Security Tests (7개)
# ============================================================================

def test_sql_injection_select():
    """TC15: SQL Injection - SELECT"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="SELECT * FROM users")

    errors = exc_info.value.errors()
    assert any("허용되지 않는 패턴" in str(error) for error in errors)


def test_sql_injection_union():
    """TC16: SQL Injection - UNION"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="test UNION SELECT password FROM users")

    errors = exc_info.value.errors()
    assert any("허용되지 않는 패턴" in str(error) for error in errors)


def test_sql_injection_drop():
    """TC17: SQL Injection - DROP"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="test; DROP TABLE users;")

    errors = exc_info.value.errors()
    assert any("허용되지 않는 패턴" in str(error) or "허용되지 않는 스크립트" in str(error) or "한글, 영어, 숫자" in str(error) for error in errors)


def test_xss_script_tag():
    """TC18: XSS - <script> 태그"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="<script>alert('xss')</script>")

    errors = exc_info.value.errors()
    assert any("스크립트" in str(error) or "한글, 영어, 숫자" in str(error) for error in errors)


def test_xss_javascript_protocol():
    """TC19: XSS - javascript: 프로토콜"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="javascript:alert(1)")

    errors = exc_info.value.errors()
    assert any("스크립트" in str(error) or "한글, 영어, 숫자" in str(error) for error in errors)


def test_disallowed_special_characters():
    """TC20: 허용되지 않는 특수문자 (#, $, %, &)"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="테스트 #해시태그 $달러")

    errors = exc_info.value.errors()
    assert any("한글, 영어, 숫자" in str(error) for error in errors)


def test_sql_comment_syntax():
    """TC21: SQL 주석 기호 (--, /*)"""
    with pytest.raises(ValidationError) as exc_info:
        SearchQueryRequest(query="test -- comment")

    errors = exc_info.value.errors()
    assert any("허용되지 않는 패턴" in str(error) or "한글, 영어, 숫자" in str(error) for error in errors)
