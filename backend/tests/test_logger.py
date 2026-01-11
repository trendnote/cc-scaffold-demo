"""
로깅 마스킹 테스트

Task 4.2: 기본 모니터링 로그 설정

개인정보 마스킹 기능 검증:
- 이메일 마스킹 (user@example.com → u***@example.com)
- IP 마스킹 (192.168.1.1 → 192.168.*.*)
- 민감 검색어 해시
- 개인정보 패턴 마스킹 (주민번호, 계좌번호, 전화번호)
"""
import pytest
from app.utils.logger import (
    mask_email,
    mask_ip,
    mask_sensitive_data
)


class TestEmailMasking:
    """이메일 마스킹 테스트"""

    def test_mask_email_standard(self):
        """표준 이메일 마스킹"""
        assert mask_email("user@example.com") == "u***@example.com"
        assert mask_email("admin@company.co.kr") == "a***@company.co.kr"

    def test_mask_email_short_local(self):
        """짧은 로컬 파트"""
        assert mask_email("a@example.com") == "*@example.com"
        assert mask_email("ab@example.com") == "a***@example.com"

    def test_mask_email_long_local(self):
        """긴 로컬 파트"""
        assert mask_email("verylongusername@example.com") == "v***@example.com"

    def test_mask_email_invalid(self):
        """잘못된 이메일"""
        # @ 없음
        assert mask_email("notanemail") == "notanemail"
        assert mask_email("") == ""

    def test_mask_email_special_chars(self):
        """특수 문자 포함"""
        assert mask_email("user.name@example.com") == "u***@example.com"
        assert mask_email("user+tag@example.com") == "u***@example.com"


class TestIPMasking:
    """IP 주소 마스킹 테스트"""

    def test_mask_ip_standard(self):
        """표준 IPv4 마스킹"""
        assert mask_ip("192.168.1.1") == "192.168.*.*"
        assert mask_ip("10.0.0.1") == "10.0.*.*"
        assert mask_ip("172.16.0.100") == "172.16.*.*"

    def test_mask_ip_public(self):
        """공용 IP 마스킹"""
        assert mask_ip("8.8.8.8") == "8.8.*.*"
        assert mask_ip("1.1.1.1") == "1.1.*.*"

    def test_mask_ip_invalid(self):
        """잘못된 IP"""
        # 4개 옥텟이 아님
        assert mask_ip("192.168.1") == "192.168.1"
        assert mask_ip("notanip") == "notanip"
        assert mask_ip("") == ""


class TestSensitiveDataMasking:
    """민감 데이터 마스킹 프로세서 테스트"""

    def test_mask_email_field(self):
        """이메일 필드 마스킹"""
        event_dict = {"email": "user@example.com", "other": "data"}
        result = mask_sensitive_data(None, None, event_dict)

        assert result["email"] == "u***@example.com"
        assert result["other"] == "data"

    def test_mask_user_email_field(self):
        """user_email 필드 마스킹"""
        event_dict = {"user_email": "admin@company.com"}
        result = mask_sensitive_data(None, None, event_dict)

        assert result["user_email"] == "a***@company.com"

    def test_mask_client_ip_field(self):
        """client_ip 필드 마스킹"""
        event_dict = {"client_ip": "192.168.1.100"}
        result = mask_sensitive_data(None, None, event_dict)

        assert result["client_ip"] == "192.168.*.*"

    def test_mask_sensitive_query_keyword(self):
        """민감 키워드 포함 검색어 해시"""
        event_dict = {"query": "급여 명세서 조회"}
        result = mask_sensitive_data(None, None, event_dict)

        # SHA-256 해시 (16자)
        assert len(result["query"]) == 16
        assert result["query_masked"] is True

    def test_mask_sensitive_query_keywords(self):
        """여러 민감 키워드"""
        test_cases = [
            "급여 조회",
            "연봉 협상",
            "인사 평가",
            "기밀 문서",
            "비밀번호",
            "급여명세서",
            "성과급 지급"
        ]

        for query in test_cases:
            event_dict = {"query": query}
            result = mask_sensitive_data(None, None, event_dict)

            assert len(result["query"]) == 16, f"Failed for: {query}"
            assert result["query_masked"] is True

    def test_mask_query_ssn_pattern(self):
        """주민번호 패턴 마스킹"""
        event_dict = {"query": "주민번호 123456-1234567로 조회"}
        result = mask_sensitive_data(None, None, event_dict)

        assert "[주민번호]" in result["query"]
        assert "123456-1234567" not in result["query"]

    def test_mask_query_account_pattern(self):
        """계좌번호 패턴 마스킹"""
        event_dict = {"query": "계좌 123-456-789012 확인"}
        result = mask_sensitive_data(None, None, event_dict)

        assert "[계좌번호]" in result["query"]
        assert "123-456-789012" not in result["query"]

    def test_mask_query_phone_pattern(self):
        """전화번호 패턴 마스킹"""
        event_dict = {"query": "전화 010-1234-5678로 연락"}
        result = mask_sensitive_data(None, None, event_dict)

        assert "[전화번호]" in result["query"]
        assert "010-1234-5678" not in result["query"]

    def test_mask_query_phone_no_hyphen(self):
        """하이픈 없는 전화번호"""
        event_dict = {"query": "01012345678로 문자"}
        result = mask_sensitive_data(None, None, event_dict)

        assert "[전화번호]" in result["query"]
        assert "01012345678" not in result["query"]

    def test_mask_query_email_pattern(self):
        """검색어 내 이메일 주소 마스킹"""
        event_dict = {"query": "user@example.com으로 이메일 전송"}
        result = mask_sensitive_data(None, None, event_dict)

        assert "[이메일]" in result["query"]
        assert "user@example.com" not in result["query"]

    def test_no_masking_normal_query(self):
        """일반 검색어는 마스킹하지 않음"""
        event_dict = {"query": "연차 사용 방법"}
        result = mask_sensitive_data(None, None, event_dict)

        assert result["query"] == "연차 사용 방법"
        assert "query_masked" not in result

    def test_multiple_fields_masking(self):
        """여러 필드 동시 마스킹"""
        event_dict = {
            "email": "user@example.com",
            "client_ip": "192.168.1.1",
            "query": "급여 조회",
            "other_field": "not masked"
        }
        result = mask_sensitive_data(None, None, event_dict)

        assert result["email"] == "u***@example.com"
        assert result["client_ip"] == "192.168.*.*"
        assert len(result["query"]) == 16  # 해시
        assert result["query_masked"] is True
        assert result["other_field"] == "not masked"


class TestMaskingEdgeCases:
    """엣지 케이스 테스트"""

    def test_empty_event_dict(self):
        """빈 이벤트 딕셔너리"""
        event_dict = {}
        result = mask_sensitive_data(None, None, event_dict)

        assert result == {}

    def test_none_values(self):
        """None 값"""
        event_dict = {
            "email": None,
            "client_ip": None,
            "query": None
        }
        # str() 변환으로 "None" 문자열이 됨
        result = mask_sensitive_data(None, None, event_dict)

        # None은 str()로 "None" 변환되므로 마스킹 시도
        # 이메일/IP 형식이 아니므로 그대로 유지
        assert result["email"] == "None"
        assert result["client_ip"] == "None"
        assert result["query"] == "None"

    def test_numeric_values(self):
        """숫자 값"""
        event_dict = {
            "email": 12345,
            "client_ip": 67890,
            "query": 999
        }
        result = mask_sensitive_data(None, None, event_dict)

        # str() 변환 후 이메일/IP 형식이 아니므로 그대로
        assert result["email"] == "12345"
        assert result["client_ip"] == "67890"
        assert result["query"] == "999"

    def test_unicode_query(self):
        """유니코드 검색어"""
        event_dict = {"query": "한글 검색어 😀 emoji"}
        result = mask_sensitive_data(None, None, event_dict)

        assert result["query"] == "한글 검색어 😀 emoji"

    def test_mixed_sensitive_and_patterns(self):
        """민감 키워드 + 개인정보 패턴"""
        event_dict = {"query": "급여명세서 010-1234-5678로 전송"}
        result = mask_sensitive_data(None, None, event_dict)

        # 민감 키워드가 우선 → 해시
        assert len(result["query"]) == 16
        assert result["query_masked"] is True


class TestMaskingIntegration:
    """통합 테스트"""

    def test_realistic_log_event(self):
        """실제 로그 이벤트 시뮬레이션"""
        event_dict = {
            "event": "search_request",
            "user_id": "user_12345",
            "email": "user@example.com",
            "client_ip": "192.168.1.100",
            "query": "연차 사용 방법",
            "results_count": 5,
            "response_time_ms": 1234
        }

        result = mask_sensitive_data(None, None, event_dict)

        # 마스킹 확인
        assert result["email"] == "u***@example.com"
        assert result["client_ip"] == "192.168.*.*"

        # 일반 필드는 유지
        assert result["event"] == "search_request"
        assert result["user_id"] == "user_12345"
        assert result["query"] == "연차 사용 방법"
        assert result["results_count"] == 5
        assert result["response_time_ms"] == 1234

    def test_error_log_event(self):
        """에러 로그 이벤트"""
        event_dict = {
            "event": "authentication_failed",
            "email": "admin@company.com",
            "client_ip": "10.0.0.1",
            "error": "Invalid credentials",
            "timestamp": "2025-01-11T10:30:00Z"
        }

        result = mask_sensitive_data(None, None, event_dict)

        assert result["email"] == "a***@company.com"
        assert result["client_ip"] == "10.0.*.*"
        assert result["error"] == "Invalid credentials"
        assert result["timestamp"] == "2025-01-11T10:30:00Z"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
