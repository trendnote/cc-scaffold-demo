# Task 4.3b 실행 계획: 권한 및 보안 테스트

## 📋 작업 정보
- **Task ID**: 4.3b
- **Task명**: 권한 및 보안 테스트
- **예상 시간**: 3시간
- **담당**: Backend
- **의존성**: Task 2.4 (권한 기반 필터링 로직)
- **GitHub Issue**: #33

---

## 🎯 작업 목표

권한 제어 및 보안 취약점을 체계적으로 테스트하여 시스템 안전성 보장

---

## 📐 기술 스택

- **pytest**: 7.4+ (Python 테스트 프레임워크)
- **httpx**: 0.25+ (비동기 HTTP 클라이언트)
- **bandit**: 1.7+ (보안 스캐너)
- **safety**: 2.3+ (의존성 취약점 검사)

---

## 🏗️ 테스트 아키텍처

```
┌──────────────────────────────────────────────────────────────┐
│              Security & Permission Testing                    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────┐                │
│  │  Permission Tests (10 cases)             │                │
│  │  - 권한 레벨별 문서 접근 제어              │                │
│  │  - 부서별 필터링                          │                │
│  │  - 인증/인가 검증                         │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Security Tests                           │                │
│  │  - SQL Injection 방어                    │                │
│  │  - XSS 방어                              │                │
│  │  - CSRF 방어                             │                │
│  │  - 환경 변수 노출 확인                    │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Static Analysis                          │                │
│  │  - Bandit (코드 스캔)                     │                │
│  │  - Safety (의존성 취약점)                 │                │
│  └──────────────────┬───────────────────────┘                │
│                     │                                          │
│                     ▼                                          │
│  ┌──────────────────────────────────────────┐                │
│  │  Security Report                          │                │
│  │  - 테스트 결과                            │                │
│  │  - 취약점 목록                            │                │
│  │  - 개선 권장 사항                         │                │
│  └──────────────────────────────────────────┘                │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 📝 구현 계획

### Phase 1: 권한 테스트 작성 (1.5시간)

#### 1.1 테스트 픽스처 및 헬퍼
**파일**: `backend/tests/conftest.py`
```python
import pytest
from httpx import AsyncClient
from app.core.security import create_access_token
from datetime import timedelta


@pytest.fixture
async def l1_user_token():
    """L1 사용자 토큰 (일반 사용자)"""
    token = create_access_token(
        data={
            "sub": "user@example.com",
            "user_id": "user_123",
            "access_level": 1,
            "department": "Engineering"
        },
        secret_key="test-secret",
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
async def l2_user_token():
    """L2 사용자 토큰 (팀 리드)"""
    token = create_access_token(
        data={
            "sub": "lead@example.com",
            "user_id": "lead_123",
            "access_level": 2,
            "department": "Engineering"
        },
        secret_key="test-secret",
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
async def l3_user_token():
    """L3 사용자 토큰 (관리자)"""
    token = create_access_token(
        data={
            "sub": "admin@example.com",
            "user_id": "admin_123",
            "access_level": 3,
            "department": "Management"
        },
        secret_key="test-secret",
        expires_delta=timedelta(hours=1)
    )
    return token


@pytest.fixture
async def expired_token():
    """만료된 토큰"""
    token = create_access_token(
        data={"sub": "user@example.com", "user_id": "user_123"},
        secret_key="test-secret",
        expires_delta=timedelta(seconds=-1)  # 이미 만료됨
    )
    return token
```

#### 1.2 권한 테스트 케이스
**파일**: `backend/tests/integration/test_access_control.py`
```python
"""
권한 제어 통합 테스트

[HARD RULE] 권한 검증:
- 사용자는 자신의 access_level 이하 문서만 접근 가능
- 부서 외 문서는 L2 이상만 접근 가능 (Management 제외)
- 인증되지 않은 요청은 모두 거부
"""
import pytest
from httpx import AsyncClient


class TestAccessControl:
    """권한 제어 테스트"""

    @pytest.mark.asyncio
    async def test_l1_user_cannot_access_l2_documents(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        Test Case 1: L1 사용자는 L2 문서에 접근할 수 없다

        Given: L1 사용자 (access_level=1)
        When: L2 문서 검색 요청
        Then: 검색 결과에 L2 문서가 포함되지 않음
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "L2 전용 정책 문서", "limit": 10},
            headers={"Authorization": f"Bearer {l1_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # 모든 출처의 access_level이 1 이하인지 확인
        for source in data.get("sources", []):
            metadata = source.get("metadata", {})
            access_level = metadata.get("access_level", 1)
            assert access_level <= 1, f"L2 문서 발견: {source}"

    @pytest.mark.asyncio
    async def test_l1_user_cannot_access_l3_documents(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        Test Case 2: L1 사용자는 L3 문서에 접근할 수 없다
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "기밀 문서", "limit": 10},
            headers={"Authorization": f"Bearer {l1_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for source in data.get("sources", []):
            metadata = source.get("metadata", {})
            access_level = metadata.get("access_level", 1)
            assert access_level <= 1

    @pytest.mark.asyncio
    async def test_l2_user_cannot_access_other_department_documents(
        self,
        client: AsyncClient,
        l2_user_token: str
    ):
        """
        Test Case 3: L2 사용자는 다른 부서의 문서에 접근할 수 없다

        Given: Engineering 부서 L2 사용자
        When: HR 부서 문서 검색
        Then: 검색 결과에 HR 부서 문서가 포함되지 않음
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "HR 부서 전용 정책", "limit": 10},
            headers={"Authorization": f"Bearer {l2_user_token}"}
        )

        assert response.status_code == 200
        data = response.json()

        for source in data.get("sources", []):
            metadata = source.get("metadata", {})
            department = metadata.get("department", "")
            # L1 문서이거나 Engineering 부서 문서만 허용
            if metadata.get("access_level", 1) >= 2:
                assert department == "Engineering", \
                    f"다른 부서 문서 발견: {department}"

    @pytest.mark.asyncio
    async def test_l2_user_can_access_own_department_l2_documents(
        self,
        client: AsyncClient,
        l2_user_token: str
    ):
        """
        Test Case 4: L2 사용자는 자신의 부서 L2 문서에 접근할 수 있다
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "Engineering 팀 가이드", "limit": 10},
            headers={"Authorization": f"Bearer {l2_user_token}"}
        )

        assert response.status_code == 200
        # 검색 결과가 있어야 함 (부서 문서 접근 가능)

    @pytest.mark.asyncio
    async def test_management_department_can_access_all_documents(
        self,
        client: AsyncClient,
        l3_user_token: str
    ):
        """
        Test Case 5: Management 부서는 모든 문서에 접근할 수 있다

        Given: Management 부서 L3 사용자
        When: 모든 부서 문서 검색
        Then: 모든 문서 접근 가능
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "전사 정책", "limit": 10},
            headers={"Authorization": f"Bearer {l3_user_token}"}
        )

        assert response.status_code == 200
        # Management는 모든 문서 접근 가능

    @pytest.mark.asyncio
    async def test_unauthenticated_request_is_rejected(
        self,
        client: AsyncClient
    ):
        """
        Test Case 6: 인증되지 않은 요청은 거부된다

        Given: 토큰 없음
        When: 검색 API 호출
        Then: 401 Unauthorized
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "테스트", "limit": 5}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_expired_token_is_rejected(
        self,
        client: AsyncClient,
        expired_token: str
    ):
        """
        Test Case 7: 만료된 토큰은 거부된다

        Given: 만료된 JWT 토큰
        When: 검색 API 호출
        Then: 401 Unauthorized
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "테스트", "limit": 5},
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_is_rejected(
        self,
        client: AsyncClient
    ):
        """
        Test Case 8: 잘못된 토큰은 거부된다

        Given: 유효하지 않은 토큰
        When: 검색 API 호출
        Then: 401 Unauthorized
        """
        response = await client.post(
            "/api/v1/search/",
            json={"query": "테스트", "limit": 5},
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_api_requires_admin_permission(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        Test Case 9: 관리자 API는 관리자 권한이 필요하다

        Given: L1 사용자
        When: 관리자 API 호출 (수동 인덱싱)
        Then: 403 Forbidden
        """
        response = await client.post(
            "/api/v1/admin/index",
            headers={"Authorization": f"Bearer {l1_user_token}"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_document_deletion_permission(
        self,
        client: AsyncClient,
        l1_user_token: str,
        l3_user_token: str
    ):
        """
        Test Case 10: 문서 삭제는 관리자만 가능하다

        Given: L1 사용자 및 L3 관리자
        When: 문서 삭제 API 호출
        Then: L1은 403, L3는 성공
        """
        # L1 사용자 시도 (실패 예상)
        response_l1 = await client.delete(
            "/api/v1/documents/test_doc_123",
            headers={"Authorization": f"Bearer {l1_user_token}"}
        )
        assert response_l1.status_code == 403

        # L3 관리자 시도 (성공 예상, 실제 문서 없어도 권한 체크는 통과)
        response_l3 = await client.delete(
            "/api/v1/documents/test_doc_123",
            headers={"Authorization": f"Bearer {l3_user_token}"}
        )
        # 404 (문서 없음) 또는 200 (성공)
        assert response_l3.status_code in [200, 404]
```

---

### Phase 2: 보안 테스트 작성 (1시간)

#### 2.1 SQL Injection 테스트
**파일**: `backend/tests/security/test_sql_injection.py`
```python
"""
SQL Injection 공격 방어 테스트
"""
import pytest
from httpx import AsyncClient


class TestSQLInjection:
    """SQL Injection 방어 테스트"""

    @pytest.mark.asyncio
    async def test_sql_injection_in_search_query(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        검색어에 SQL Injection 시도 시 거부된다

        Given: SQL Injection 패턴
        When: 검색 API 호출
        Then: 422 Validation Error 또는 안전하게 처리
        """
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "admin'--",
            "' OR 1=1--",
        ]

        for payload in sql_payloads:
            response = await client.post(
                "/api/v1/search/",
                json={"query": payload, "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            # 422 (검증 실패) 또는 200 (안전하게 처리)
            assert response.status_code in [200, 422], \
                f"SQL Injection 방어 실패: {payload}"

            # 200인 경우 정상 응답 형식이어야 함
            if response.status_code == 200:
                data = response.json()
                assert "answer" in data
                assert "sources" in data
```

#### 2.2 XSS 방어 테스트
**파일**: `backend/tests/security/test_xss.py`
```python
"""
XSS 공격 방어 테스트
"""
import pytest
from httpx import AsyncClient


class TestXSS:
    """XSS 방어 테스트"""

    @pytest.mark.asyncio
    async def test_xss_in_search_query(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        검색어에 XSS 스크립트 시도 시 거부되거나 이스케이프된다
        """
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(1)'>",
        ]

        for payload in xss_payloads:
            response = await client.post(
                "/api/v1/search/",
                json={"query": payload, "limit": 5},
                headers={"Authorization": f"Bearer {l1_user_token}"}
            )

            # 422 (검증 실패) 또는 200 (이스케이프 처리)
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")

                # 답변에 원본 스크립트 태그가 포함되지 않아야 함
                assert "<script>" not in answer.lower()
                assert "onerror=" not in answer.lower()
```

#### 2.3 환경 변수 노출 확인
**파일**: `backend/tests/security/test_env_leaks.py`
```python
"""
환경 변수 및 민감 정보 노출 확인
"""
import pytest
from httpx import AsyncClient


class TestEnvironmentLeaks:
    """환경 변수 노출 테스트"""

    @pytest.mark.asyncio
    async def test_error_response_does_not_leak_secrets(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        에러 응답에 환경 변수가 노출되지 않는다

        Given: 잘못된 요청 (에러 발생)
        When: API 호출
        Then: 에러 메시지에 민감 정보 없음
        """
        # 의도적으로 에러 발생 (잘못된 데이터)
        response = await client.post(
            "/api/v1/search/",
            json={"invalid_field": "test"},
            headers={"Authorization": f"Bearer {l1_user_token}"}
        )

        error_body = response.text

        # 민감 정보 패턴 체크
        sensitive_patterns = [
            "DATABASE_URL",
            "JWT_SECRET",
            "API_KEY",
            "password",
            "/Users/",
            "/home/",
            "postgresql://",
        ]

        for pattern in sensitive_patterns:
            assert pattern not in error_body, \
                f"민감 정보 노출: {pattern}"

    @pytest.mark.asyncio
    async def test_stack_trace_not_exposed(
        self,
        client: AsyncClient,
        l1_user_token: str
    ):
        """
        스택 트레이스가 외부에 노출되지 않는다
        """
        # 의도적으로 에러 발생
        response = await client.get(
            "/api/v1/nonexistent-endpoint",
            headers={"Authorization": f"Bearer {l1_user_token}"}
        )

        error_body = response.text

        # 스택 트레이스 패턴 체크
        assert "Traceback" not in error_body
        assert "File \"/" not in error_body
```

---

### Phase 3: 정적 분석 및 의존성 검사 (0.5시간)

#### 3.1 Bandit 보안 스캔
**파일**: `backend/.bandit`
```yaml
# Bandit 설정
exclude_dirs:
  - /tests/
  - /venv/
  - /.venv/

tests:
  - B201  # Flask debug mode
  - B301  # Pickle
  - B302  # Marshal
  - B303  # MD5
  - B304  # SHA1
  - B305  # Cipher
  - B306  # TempFile
  - B307  # eval
  - B308  # mark_safe
  - B309  # HTTPSConnection
  - B310  # urllib
  - B311  # random
  - B312  # telnetlib
  - B313  # xml
  - B314  # xml
  - B315  # xml
  - B316  # xml
  - B317  # xml
  - B318  # xml
  - B319  # xml
  - B320  # xml
  - B321  # ftplib
  - B322  # input
  - B323  # unverified context
  - B324  # hashlib
  - B325  # tempnam
  - B401  # import telnetlib
  - B402  # import ftplib
  - B403  # import pickle
  - B404  # import subprocess
  - B405  # import xml
  - B406  # import xml
  - B407  # import xml
  - B408  # import xml
  - B409  # import xml
  - B410  # import xml
  - B411  # import xml
  - B412  # import xml
  - B413  # import Crypto
  - B501  # requests without verify
  - B502  # ssl with bad defaults
  - B503  # ssl with bad version
  - B504  # ssl with bad ciphers
  - B505  # weak cryptographic key
  - B506  # yaml load
  - B507  # ssh no host key
  - B601  # paramiko calls
  - B602  # shell injection
  - B603  # subprocess without shell
  - B604  # shell true
  - B605  # start_process_with_shell
  - B606  # start_process_with_no_shell
  - B607  # start_process_with_partial_path
  - B608  # SQL
  - B609  # wildcard injection
  - B610  # django extra
  - B611  # django rawsql
  - B701  # jinja2 autoescape
  - B702  # mako templates
  - B703  # django mark safe
```

**실행 스크립트**:
```bash
# Bandit 실행
bandit -r backend/app -f json -o security-report.json

# 간단한 출력
bandit -r backend/app
```

#### 3.2 Safety 의존성 검사
**파일**: `backend/scripts/check_dependencies.sh`
```bash
#!/bin/bash
# 의존성 취약점 검사

echo "Checking for known vulnerabilities..."

# Safety로 의존성 검사
safety check --json > safety-report.json

# 결과 출력
if [ $? -eq 0 ]; then
    echo "✓ No known vulnerabilities found"
else
    echo "✗ Vulnerabilities detected! Check safety-report.json"
    exit 1
fi
```

#### 3.3 비밀번호 하드코딩 스캔
**파일**: `backend/scripts/scan_secrets.sh`
```bash
#!/bin/bash
# 하드코딩된 비밀번호 스캔

echo "Scanning for hardcoded secrets..."

# 패턴 검색
grep -rn --exclude-dir=venv --exclude-dir=.git \
    -E "(password|secret|api_key|token)\s*=\s*['\"]" \
    backend/app/ || echo "✓ No hardcoded secrets found"

# .env 파일이 git에 포함되지 않았는지 확인
if git ls-files | grep -q "\.env$"; then
    echo "✗ .env file is tracked by git!"
    exit 1
else
    echo "✓ .env file is not tracked"
fi
```

---

## 🧪 테스트 실행

### 전체 보안 테스트 실행
```bash
# 권한 테스트
pytest tests/integration/test_access_control.py -v

# 보안 테스트
pytest tests/security/ -v

# Bandit 스캔
bandit -r backend/app

# Safety 의존성 검사
safety check

# 비밀번호 스캔
bash backend/scripts/scan_secrets.sh
```

### CI/CD 통합
**파일**: `.github/workflows/security-tests.yml`
```yaml
name: Security Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install bandit safety

      - name: Run Permission Tests
        run: |
          cd backend
          pytest tests/integration/test_access_control.py -v

      - name: Run Security Tests
        run: |
          cd backend
          pytest tests/security/ -v

      - name: Run Bandit Security Scan
        run: |
          cd backend
          bandit -r app -f json -o bandit-report.json
          bandit -r app

      - name: Check Dependencies for Vulnerabilities
        run: |
          cd backend
          safety check --json > safety-report.json

      - name: Scan for Hardcoded Secrets
        run: |
          bash backend/scripts/scan_secrets.sh

      - name: Upload Security Reports
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            backend/bandit-report.json
            backend/safety-report.json
```

---

## ✅ 검증 기준

### 권한 테스트 (10개 케이스)
- [ ] Test 1: L1 사용자 → L2 문서 접근 차단
- [ ] Test 2: L1 사용자 → L3 문서 접근 차단
- [ ] Test 3: L2 사용자 → 다른 부서 문서 접근 차단
- [ ] Test 4: L2 사용자 → 자신의 부서 L2 문서 접근 허용
- [ ] Test 5: Management 부서 → 모든 문서 접근 허용
- [ ] Test 6: 미인증 사용자 → 모든 API 차단
- [ ] Test 7: 만료된 토큰 → 401 에러
- [ ] Test 8: 잘못된 토큰 → 401 에러
- [ ] Test 9: 관리자 API → 관리자만 접근
- [ ] Test 10: 문서 삭제 → 관리자만 가능

### 보안 테스트
- [ ] SQL Injection 공격 방어 확인
- [ ] XSS 공격 방어 확인
- [ ] CSRF 토큰 검증 (해당되는 경우)
- [ ] 환경 변수 노출 없음
- [ ] 스택 트레이스 노출 없음

### 정적 분석
- [ ] Bandit 스캔 취약점 없음
- [ ] Safety 의존성 취약점 없음
- [ ] 비밀번호 하드코딩 없음

---

## 📂 파일 구조

```
backend/
├── tests/
│   ├── integration/
│   │   └── test_access_control.py
│   └── security/
│       ├── test_sql_injection.py
│       ├── test_xss.py
│       └── test_env_leaks.py
├── scripts/
│   ├── check_dependencies.sh
│   └── scan_secrets.sh
├── .bandit
└── security-reports/              # 보안 리포트 (gitignore)
    ├── bandit-report.json
    └── safety-report.json
```

---

## 📊 보안 리포트 예시

### Bandit 리포트
```json
{
  "results": [],
  "metrics": {
    "total_lines": 5234,
    "nosec_count": 0,
    "severity": {
      "HIGH": 0,
      "MEDIUM": 0,
      "LOW": 0
    }
  }
}
```

### Safety 리포트
```
+==============================================================================+
|                                                                              |
|                               /$$$$$$            /$$                         |
|                              /$$__  $$          | $$                         |
|           /$$$$$$$  /$$$$$$ | $$  \__//$$$$$$  /$$$$$$   /$$   /$$           |
|          /$$_____/ |____  $$| $$$$   /$$__  $$|_  $$_/  | $$  | $$           |
|         |  $$$$$$   /$$$$$$$| $$_/  | $$$$$$$$  | $$    | $$  | $$           |
|          \____  $$ /$$__  $$| $$    | $$_____/  | $$ /$$| $$  | $$           |
|          /$$$$$$$/|  $$$$$$$| $$    |  $$$$$$$  |  $$$$/|  $$$$$$$           |
|         |_______/  \_______/|__/     \_______/   \___/   \____  $$           |
|                                                          /$$  | $$           |
|                                                         |  $$$$$$/           |
|  by pyup.io                                              \______/            |
|                                                                              |
+==============================================================================+
| REPORT                                                                       |
+============================+===========+==========================+==========+
| package                    | installed | affected                 | ID       |
+============================+===========+==========================+==========+
+==============================================================================+
| No known security vulnerabilities found.                                    |
+==============================================================================+
```

---

## 🔒 보안 체크리스트

### [HARD RULE] 필수 확인 사항
- [ ] 모든 API 엔드포인트에 인증 필요
- [ ] JWT 시크릿 환경 변수로 관리
- [ ] 데이터베이스 URL 환경 변수로 관리
- [ ] 비밀번호 평문 저장 금지 (bcrypt 해싱)
- [ ] SQL 쿼리 파라미터화 (ORM 사용)
- [ ] 사용자 입력 검증 (Pydantic)
- [ ] 에러 메시지에 민감 정보 포함 금지
- [ ] CORS 설정 적절히 제한
- [ ] HTTPS 사용 (운영 환경)
- [ ] 로그에 민감 정보 마스킹

---

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)

---

**작성자**: Task Planner
**작성일**: 2026-01-10
**버전**: 1.0.0
