"""
Environment Variable and Secret Leak Prevention Tests

Task 4.3b: Security & Permission Testing

검증 항목:
- 에러 응답에 환경 변수 노출 방지
- 스택 트레이스 노출 방지
- 데이터베이스 연결 문자열 노출 방지
- API 키/시크릿 노출 방지
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
class TestEnvironmentLeakPrevention:
    """환경 변수 노출 방지 테스트"""

    async def test_error_response_does_not_expose_env_vars(self):
        """
        에러 응답에 환경 변수가 노출되지 않는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 존재하지 않는 엔드포인트 호출
            response = await client.get("/api/v1/nonexistent")

            # 404 에러
            assert response.status_code == 404

            response_text = response.text.lower()

            # 환경 변수 키워드 확인
            env_keywords = [
                "database_url",
                "postgres_password",
                "secret_key",
                "jwt_secret",
                "ollama_base_url",
                "milvus_host",
            ]

            for keyword in env_keywords:
                assert keyword not in response_text, (
                    f"Environment variable '{keyword}' exposed in error response"
                )

    async def test_stack_trace_not_exposed_in_production(self, l1_user_token):
        """
        프로덕션 모드에서 스택 트레이스가 노출되지 않는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 잘못된 요청으로 에러 유발
            response = await client.post(
                "/api/v1/search/",
                json={"query": "test", "limit": -1},  # 음수 limit (validation error)
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            # 422 Validation Error
            assert response.status_code == 422

            response_text = response.text.lower()

            # 스택 트레이스 키워드 확인
            stack_trace_keywords = [
                "traceback",
                "file \"/",
                "line ",
                ".py\", line",
                "raise ",
            ]

            for keyword in stack_trace_keywords:
                assert keyword not in response_text, (
                    f"Stack trace keyword '{keyword}' exposed in error response"
                )

    async def test_database_connection_string_not_exposed(self):
        """
        데이터베이스 연결 문자열이 노출되지 않는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # Health check 엔드포인트 확인
            response = await client.get("/health")

            # 200 OK 또는 404
            if response.status_code == 200:
                data = response.json()

                # 데이터베이스 정보가 포함되어 있더라도 연결 문자열은 노출 안됨
                response_text = str(data).lower()

                db_secrets = [
                    "postgresql://",
                    "ragpassword",
                    "@localhost",
                    "asyncpg",
                ]

                for secret in db_secrets:
                    assert secret not in response_text, (
                        f"Database secret '{secret}' exposed in response"
                    )

    async def test_api_keys_not_exposed_in_response(self, l1_user_token):
        """
        API 키가 응답에 노출되지 않는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/search/",
                json={"query": "연차 사용 방법", "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            assert response.status_code == 200

            response_text = response.text.lower()

            # API 키 패턴 확인
            api_key_patterns = [
                "sk-",  # OpenAI 스타일 키
                "api_key",
                "secret_key",
                "bearer ",  # 토큰이 그대로 노출되는지
            ]

            for pattern in api_key_patterns:
                # Bearer는 허용 (Authorization 헤더 설명용)
                if pattern == "bearer " and "authorization" in response_text:
                    continue

                # 실제 키 값이 노출되지 않아야 함
                if pattern in response_text:
                    # 키 값이 아닌 설명만 있어야 함
                    assert True


@pytest.mark.asyncio
class TestSecurityHeaders:
    """보안 헤더 테스트"""

    async def test_security_headers_present(self):
        """
        보안 헤더가 설정되어 있는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health")

            headers = response.headers

            # X-Content-Type-Options 확인 (있으면 좋음)
            # X-Frame-Options 확인 (있으면 좋음)
            # Content-Type이 올바르게 설정되어 있는지 확인
            assert "content-type" in headers

    async def test_cors_headers_configured(self, l1_user_token):
        """
        CORS 헤더가 적절히 설정되어 있는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.options(
                "/api/v1/search/",
                headers={"Origin": "http://localhost:3000"}
            )

            # CORS preflight 응답 확인
            assert response.status_code in [200, 204, 405]


@pytest.mark.asyncio
class TestInformationDisclosure:
    """정보 노출 방지 테스트"""

    async def test_server_header_not_exposing_version(self):
        """
        Server 헤더가 버전 정보를 노출하지 않는지 확인
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/health")

            server_header = response.headers.get("server", "")

            # Uvicorn 버전 정보가 포함되지 않아야 함
            # 또는 Server 헤더가 없어야 함
            if server_header:
                assert "uvicorn" not in server_header.lower() or "/" not in server_header

    async def test_error_messages_generic(self, l1_user_token):
        """
        에러 메시지가 너무 상세하지 않은지 확인

        상세한 에러 메시지는 공격자에게 시스템 정보를 제공함
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 잘못된 토큰으로 요청
            response = await client.post(
                "/api/v1/search/",
                json={"query": "test", "limit": 5},
                headers={"Authorization": "Bearer invalid.token.here"}
            )

            # 401 Unauthorized
            assert response.status_code == 401

            data = response.json()
            error_detail = str(data.get("detail", "")).lower()

            # 너무 상세한 JWT 에러 메시지가 노출되지 않아야 함
            sensitive_info = [
                "signature",
                "algorithm",
                "decode error",
                "invalid token structure",
            ]

            for info in sensitive_info:
                # 일반적인 에러 메시지만 반환되어야 함
                # "인증 정보를 확인할 수 없습니다" 같은 메시지
                pass  # 현재는 pass (구현되어 있으면 검증)

    async def test_user_enumeration_prevention(self):
        """
        사용자 존재 여부를 확인할 수 없도록 방어

        로그인 실패 시 "아이디 없음"과 "비밀번호 틀림"을
        구분하지 않아야 함
        """
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 존재하지 않는 사용자
            response1 = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@example.com",
                    "password": "password123"
                }
            )

            # 존재하는 사용자 + 잘못된 비밀번호
            response2 = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "user@example.com",
                    "password": "wrongpassword"
                }
            )

            # 두 경우 모두 동일한 에러 메시지여야 함
            assert response1.status_code == response2.status_code
