"""
SQL Injection Defense Tests

Task 4.3b: Security & Permission Testing

검증 항목:
- 검색 쿼리에 SQL injection 시도
- 파라미터에 SQL injection 시도
- ORM을 통한 안전한 쿼리 실행 확인
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestSQLInjectionDefense:
    """SQL Injection 방어 테스트"""

    @pytest.fixture
    def sql_injection_payloads(self):
        """SQL Injection 공격 페이로드"""
        return [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
            "1'; DELETE FROM documents WHERE '1'='1",
            "' OR 'a'='a",
            "1' AND 1=(SELECT COUNT(*) FROM users)--",
            "'; EXEC sp_MSForEachTable 'DROP TABLE ?'; --",
            "1' UNION SELECT NULL, username, password FROM users--",
        ]

    async def test_search_query_sql_injection(
        self, l1_user_token, sql_injection_payloads
    ):
        """
        검색 쿼리에 SQL injection 시도

        예상 결과:
        - 422 Validation Error (입력 검증 실패)
        - 또는 200 OK (안전하게 처리됨)
        - 절대 500 Internal Server Error 아님
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for payload in sql_injection_payloads:
                response = await client.post(
                    "/api/v1/search/",
                    json={"query": payload, "limit": 5},
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # 안전하게 처리되어야 함
                assert response.status_code in [200, 422], (
                    f"SQL injection payload '{payload}' caused unexpected status: "
                    f"{response.status_code}"
                )

                # 500 에러가 나면 SQL injection에 취약함
                assert response.status_code != 500, (
                    f"SQL injection payload '{payload}' caused server error"
                )

    async def test_limit_parameter_sql_injection(
        self, l1_user_token, sql_injection_payloads
    ):
        """
        Limit 파라미터에 SQL injection 시도

        예상 결과:
        - 422 Validation Error (숫자 타입 검증 실패)
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for payload in sql_injection_payloads:
                response = await client.post(
                    "/api/v1/search/",
                    json={"query": "연차 사용 방법", "limit": payload},
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # Pydantic이 타입 검증 실패로 422 반환해야 함
                assert response.status_code == 422, (
                    f"SQL injection in limit parameter was not validated: {payload}"
                )

    async def test_history_pagination_sql_injection(
        self, l1_user_token, sql_injection_payloads
    ):
        """
        히스토리 페이지네이션 파라미터에 SQL injection 시도

        예상 결과:
        - 422 Validation Error
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for payload in sql_injection_payloads:
                # page 파라미터에 injection 시도
                response = await client.get(
                    f"/api/v1/users/me/history?page={payload}&page_size=10",
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # 타입 검증 실패 또는 안전하게 처리
                assert response.status_code in [200, 422, 404], (
                    f"SQL injection in pagination was not handled: {payload}"
                )

    async def test_document_id_sql_injection(
        self, l1_user_token, sql_injection_payloads
    ):
        """
        Document ID에 SQL injection 시도

        예상 결과:
        - 404 Not Found (문서 없음)
        - 또는 422 Validation Error
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for payload in sql_injection_payloads:
                response = await client.get(
                    f"/api/v1/documents/{payload}",
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # 안전하게 처리되어야 함
                assert response.status_code in [200, 404, 422], (
                    f"SQL injection in document ID was not handled: {payload}"
                )

                # 500 에러 절대 안됨
                assert response.status_code != 500


@pytest.mark.asyncio
class TestORMSafety:
    """ORM 안전성 테스트"""

    async def test_orm_uses_parameterized_queries(self, l1_user_token):
        """
        ORM이 파라미터화된 쿼리를 사용하는지 확인

        SQLAlchemy는 기본적으로 파라미터화된 쿼리를 사용하여
        SQL injection을 방어함
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 특수 문자가 포함된 정상 검색어
            query = "회사's 정책 & 규정"

            response = await client.post(
                "/api/v1/search/",
                json={"query": query, "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            # 정상 처리되어야 함
            assert response.status_code == 200

    async def test_special_characters_handled_safely(self, l1_user_token):
        """
        특수 문자가 안전하게 처리되는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            special_chars = [
                "검색어 with ' single quote",
                '검색어 with " double quote',
                "검색어 with \\ backslash",
                "검색어 with % percent",
                "검색어 with _ underscore",
                "검색어 with ; semicolon",
                "검색어 with -- comment",
            ]

            for query in special_chars:
                response = await client.post(
                    "/api/v1/search/",
                    json={"query": query, "limit": 5},
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # 안전하게 처리되어야 함
                assert response.status_code == 200, (
                    f"Special character query failed: {query}"
                )
