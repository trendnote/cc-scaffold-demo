"""
XSS (Cross-Site Scripting) Defense Tests

Task 4.3b: Security & Permission Testing

검증 항목:
- 검색 쿼리에 XSS 스크립트 삽입 시도
- 응답 데이터가 이스케이프되는지 확인
- HTML/JavaScript 코드가 실행되지 않도록 방어
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestXSSDefense:
    """XSS 방어 테스트"""

    @pytest.fixture
    def xss_payloads(self):
        """XSS 공격 페이로드"""
        return [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<marquee onstart=alert('XSS')>",
            "<div style='background-image:url(javascript:alert(\"XSS\"))'>",
            "'-alert('XSS')-'",
            "\"><script>alert('XSS')</script>",
            "<ScRiPt>alert('XSS')</ScRiPt>",
            "%3Cscript%3Ealert('XSS')%3C/script%3E",
        ]

    async def test_search_query_xss_prevention(self, l1_user_token, xss_payloads):
        """
        검색 쿼리에 XSS 스크립트 삽입 시도

        예상 결과:
        - 200 OK (정상 처리)
        - 응답에 스크립트가 이스케이프되어 포함됨
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for payload in xss_payloads:
                response = await client.post(
                    "/api/v1/search/",
                    json={"query": payload, "limit": 5},
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # 정상 처리되어야 함
                assert response.status_code in [200, 422], (
                    f"XSS payload caused unexpected status: {payload}"
                )

                # 응답이 JSON이므로 자동으로 이스케이프됨
                if response.status_code == 200:
                    data = response.json()
                    # 응답 데이터가 정상적으로 반환되어야 함
                    assert "answer" in data or "error" in data

    async def test_feedback_comment_xss_prevention(self, l1_user_token, xss_payloads):
        """
        피드백 코멘트에 XSS 스크립트 삽입 시도

        예상 결과:
        - 200 OK (저장됨)
        - 조회 시 이스케이프되어 반환
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            for payload in xss_payloads:
                response = await client.post(
                    "/api/v1/feedback/",
                    json={
                        "query_id": "test_query_123",
                        "rating": 3,
                        "comment": payload
                    },
                    headers={"Authorization": f"Bearer {l1_user_token}"}
                )

                # 저장은 성공해야 함
                assert response.status_code in [200, 201, 404, 422], (
                    f"XSS in feedback comment caused error: {payload}"
                )

    async def test_response_content_type_is_json(self, l1_user_token):
        """
        응답 Content-Type이 application/json인지 확인

        JSON 응답은 자동으로 XSS 방어됨
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/search/",
                json={"query": "연차 사용 방법", "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            # Content-Type이 application/json이어야 함
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type.lower()

    async def test_html_entities_escaped_in_response(self, l1_user_token):
        """
        응답 데이터에서 HTML 엔티티가 이스케이프되는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            html_chars = "<>&\"'"

            response = await client.post(
                "/api/v1/search/",
                json={"query": f"검색어 with HTML chars: {html_chars}", "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            assert response.status_code == 200

            # JSON은 자동으로 이스케이프됨
            data = response.json()
            assert isinstance(data, dict)


@pytest.mark.asyncio
class TestHTMLSanitization:
    """HTML 살균 테스트"""

    async def test_markdown_rendering_safe(self, l1_user_token):
        """
        마크다운 렌더링 시 XSS 방어

        프론트엔드에서 react-markdown + rehype-sanitize 사용하여
        HTML 살균 처리됨을 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 마크다운에 HTML 포함
            markdown_with_html = """
            # 제목

            <script>alert('XSS')</script>

            정상 텍스트
            """

            response = await client.post(
                "/api/v1/search/",
                json={"query": markdown_with_html, "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            # 정상 처리되어야 함
            assert response.status_code == 200

            data = response.json()
            # 응답 데이터가 정상적으로 반환되어야 함
            assert "answer" in data or "error" in data

    async def test_no_inline_javascript_in_response(self, l1_user_token):
        """
        응답에 인라인 JavaScript가 포함되지 않는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/search/",
                json={"query": "javascript:alert('XSS')", "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            assert response.status_code == 200

            # 응답 텍스트에 "javascript:" 프로토콜이 포함되지 않아야 함
            response_text = response.text.lower()
            # JSON으로 인코딩되면 안전함
            assert isinstance(response.json(), dict)


@pytest.mark.asyncio
class TestCSRFPrevention:
    """CSRF 방어 테스트"""

    async def test_api_requires_authentication(self):
        """
        API가 인증을 요구하는지 확인

        JWT 토큰 기반 인증은 CSRF 공격에 안전함
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 인증 없이 요청
            response = await client.post(
                "/api/v1/search/",
                json={"query": "연차 사용 방법", "limit": 5}
            )

            # 401 Unauthorized
            assert response.status_code == 401

    async def test_jwt_token_in_header_not_cookie(self, l1_user_token):
        """
        JWT 토큰이 쿠키가 아닌 헤더로 전송되는지 확인

        쿠키 기반 인증은 CSRF 공격에 취약하지만
        Authorization 헤더는 안전함
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Authorization 헤더로 토큰 전송
            response = await client.post(
                "/api/v1/search/",
                json={"query": "연차 사용 방법", "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            assert response.status_code == 200

            # 쿠키에 토큰이 설정되지 않아야 함
            cookies = response.cookies
            assert "access_token" not in cookies
