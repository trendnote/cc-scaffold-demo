# 테스트 가이드 (Testing Guide)

## 목차

1. [테스트 전략](#테스트-전략)
2. [백엔드 테스트](#백엔드-테스트)
3. [프론트엔드 테스트](#프론트엔드-테스트)
4. [E2E 테스트](#e2e-테스트)
5. [성능 테스트](#성능-테스트)
6. [보안 테스트](#보안-테스트)

---

## 테스트 전략

### 1. 테스트 피라미드

```
       /\
      /E2E\       10% - End-to-End Tests
     /------\
    /Integr-\    30% - Integration Tests
   /----------\
  /Unit Tests \  60% - Unit Tests
 /--------------\
```

### 2. 테스트 유형

| 유형 | 도구 | 목적 | 실행 빈도 |
|------|------|------|-----------|
| **Unit** | pytest | 함수/클래스 단위 | 커밋마다 |
| **Integration** | pytest | API/DB 통합 | 푸시마다 |
| **E2E** | Playwright | 사용자 시나리오 | PR마다 |
| **Performance** | Locust | 성능/부하 | 배포 전 |
| **Security** | Bandit, Safety | 취약점 스캔 | 매일 |

### 3. 테스트 커버리지 목표

```
Overall:        80% 이상
Critical Path:  95% 이상
Utilities:      90% 이상
UI Components:  70% 이상
```

---

## 백엔드 테스트

### 1. pytest 설정

#### 설치

```bash
cd backend

# pytest 및 플러그인 설치
pip install pytest pytest-cov pytest-asyncio httpx pytest-mock
```

#### 설정 파일

```ini
# backend/pytest.ini

[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto

# 경고 필터
filterwarnings =
    error
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning

# 마커
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    security: Security tests

# Coverage 설정
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    -v
```

### 2. Unit Tests

#### 테스트 구조

```
backend/tests/
├── unit/
│   ├── test_auth.py
│   ├── test_search.py
│   ├── test_embedding.py
│   └── test_utils.py
├── integration/
│   ├── test_api_auth.py
│   ├── test_api_search.py
│   └── test_api_documents.py
├── conftest.py
└── __init__.py
```

#### 예시: Unit Test

```python
# backend/tests/unit/test_auth.py

import pytest
from app.core.security import create_access_token, verify_password, get_password_hash

class TestAuthentication:
    """인증 관련 단위 테스트"""

    def test_password_hashing(self):
        """비밀번호 해싱 및 검증"""
        password = "test123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong", hashed)

    def test_create_access_token(self):
        """JWT 토큰 생성"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.parametrize("email,expected", [
        ("test@example.com", True),
        ("invalid", False),
        ("", False),
    ])
    def test_email_validation(self, email, expected):
        """이메일 유효성 검증"""
        from app.core.validators import is_valid_email

        assert is_valid_email(email) == expected
```

#### Fixtures

```python
# backend/tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.core.config import settings

# Test Database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def test_engine():
    """테스트용 데이터베이스 엔진"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db(test_engine):
    """테스트용 데이터베이스 세션"""
    TestingSessionLocal = sessionmaker(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    """테스트용 FastAPI 클라이언트"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def auth_headers(client):
    """인증 헤더"""
    # 테스트 사용자 로그인
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "test@example.com", "password": "test123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### 3. Integration Tests

```python
# backend/tests/integration/test_api_search.py

import pytest
from fastapi import status

class TestSearchAPI:
    """검색 API 통합 테스트"""

    @pytest.mark.asyncio
    async def test_search_query_success(self, client, auth_headers):
        """검색 쿼리 성공 케이스"""
        response = client.post(
            "/api/v1/search/query",
            json={"query": "How to deploy FastAPI"},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "search_id" in data
        assert isinstance(data["sources"], list)

    @pytest.mark.asyncio
    async def test_search_query_unauthorized(self, client):
        """인증 없이 검색 시 401 에러"""
        response = client.post(
            "/api/v1/search/query",
            json={"query": "test"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_search_query_empty(self, client, auth_headers):
        """빈 쿼리 시 422 에러"""
        response = client.post(
            "/api/v1/search/query",
            json={"query": ""},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_search_performance(self, client, auth_headers):
        """검색 성능 테스트 (30초 이내)"""
        import time

        start = time.time()
        response = client.post(
            "/api/v1/search/query",
            json={"query": "test query"},
            headers=auth_headers
        )
        duration = time.time() - start

        assert response.status_code == status.HTTP_200_OK
        assert duration < 30  # 30초 이내
```

### 4. Mocking

```python
# backend/tests/unit/test_search.py

import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestSearchService:
    """검색 서비스 단위 테스트 (Mocking 사용)"""

    @pytest.mark.asyncio
    async def test_search_with_mocked_llm(self):
        """LLM 모킹하여 검색 테스트"""
        from app.services.search import SearchService

        # LLM 응답 모킹
        with patch('app.services.llm.LLMService.generate') as mock_generate:
            mock_generate.return_value = "Mocked answer"

            service = SearchService()
            result = await service.search("test query")

            assert result["answer"] == "Mocked answer"
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_mocked_milvus(self):
        """Milvus 모킹하여 검색 테스트"""
        from app.services.search import SearchService

        # Milvus 검색 결과 모킹
        mock_results = [
            {"id": 1, "text": "Document 1", "score": 0.9},
            {"id": 2, "text": "Document 2", "score": 0.8},
        ]

        with patch('app.db.milvus_client.MilvusClient.search') as mock_search:
            mock_search.return_value = mock_results

            service = SearchService()
            results = await service.search_similar("test")

            assert len(results) == 2
            assert results[0]["score"] == 0.9
```

### 5. 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 테스트 파일
pytest tests/unit/test_auth.py

# 특정 테스트 함수
pytest tests/unit/test_auth.py::TestAuthentication::test_password_hashing

# 마커로 필터링
pytest -m unit           # Unit 테스트만
pytest -m integration    # Integration 테스트만
pytest -m "not slow"     # 느린 테스트 제외

# 병렬 실행 (pytest-xdist)
pip install pytest-xdist
pytest -n auto          # CPU 코어 수만큼 병렬

# 커버리지 리포트
pytest --cov=app --cov-report=html
open htmlcov/index.html  # 리포트 확인

# 특정 커버리지만 확인
pytest --cov=app.routers --cov-report=term-missing
```

---

## 프론트엔드 테스트

### 1. Jest 설정

#### 설치

```bash
cd frontend

# Jest 및 Testing Library 설치
npm install --save-dev jest @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install --save-dev @types/jest ts-jest
```

#### 설정 파일

```javascript
// frontend/jest.config.js

const nextJest = require('next/jest')

const createJestConfig = nextJest({
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'app/**/*.{js,jsx,ts,tsx}',
    'components/**/*.{js,jsx,ts,tsx}',
    'lib/**/*.{js,jsx,ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

```javascript
// frontend/jest.setup.js

import '@testing-library/jest-dom'

// Mock environment variables
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
```

### 2. Component Tests

```typescript
// frontend/components/search/__tests__/SearchBox.test.tsx

import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchBox from '../SearchBox'

describe('SearchBox', () => {
  it('renders search input', () => {
    render(<SearchBox onSearch={jest.fn()} />)

    const input = screen.getByPlaceholderText(/search/i)
    expect(input).toBeInTheDocument()
  })

  it('calls onSearch when submitted', async () => {
    const onSearch = jest.fn()
    render(<SearchBox onSearch={onSearch} />)

    const input = screen.getByPlaceholderText(/search/i)
    const button = screen.getByRole('button', { name: /search/i })

    await userEvent.type(input, 'test query')
    await userEvent.click(button)

    expect(onSearch).toHaveBeenCalledWith('test query')
  })

  it('shows validation error for empty input', async () => {
    render(<SearchBox onSearch={jest.fn()} />)

    const button = screen.getByRole('button', { name: /search/i })
    await userEvent.click(button)

    const error = await screen.findByText(/please enter a search query/i)
    expect(error).toBeInTheDocument()
  })

  it('disables button during loading', () => {
    render(<SearchBox onSearch={jest.fn()} isLoading={true} />)

    const button = screen.getByRole('button', { name: /searching/i })
    expect(button).toBeDisabled()
  })
})
```

### 3. API Mocking

```typescript
// frontend/lib/__tests__/api.test.ts

import { searchQuery } from '../api'

// Fetch mock
global.fetch = jest.fn()

describe('API', () => {
  beforeEach(() => {
    (fetch as jest.Mock).mockClear()
  })

  it('searchQuery success', async () => {
    const mockResponse = {
      answer: 'Test answer',
      sources: [],
      search_id: '123',
    }

    ;(fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    const result = await searchQuery('test', 'token')

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/search/query',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer token',
        },
        body: JSON.stringify({ query: 'test' }),
      })
    )

    expect(result).toEqual(mockResponse)
  })

  it('searchQuery handles error', async () => {
    ;(fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))

    await expect(searchQuery('test', 'token')).rejects.toThrow('Network error')
  })
})
```

### 4. 테스트 실행

```bash
# 모든 테스트 실행
npm test

# Watch 모드
npm test -- --watch

# 커버리지
npm test -- --coverage

# 특정 파일만
npm test SearchBox.test.tsx

# 업데이트 모드 (스냅샷)
npm test -- -u
```

---

## E2E 테스트

### 1. Playwright 설정

#### 설치

```bash
cd frontend

# Playwright 설치
npm install --save-dev @playwright/test
npx playwright install
```

#### 설정 파일

```typescript
// frontend/playwright.config.ts

import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### 2. E2E 테스트 작성

```typescript
// frontend/tests/e2e/search.spec.ts

import { test, expect } from '@playwright/test'

test.describe('Search Flow', () => {
  test.beforeEach(async ({ page }) => {
    // 로그인
    await page.goto('/login')
    await page.fill('input[name="email"]', 'test@example.com')
    await page.fill('input[name="password"]', 'test123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/search')
  })

  test('complete search flow', async ({ page }) => {
    // 검색 페이지 확인
    await expect(page).toHaveURL('/search')

    // 검색 입력
    await page.fill('input[placeholder*="Search"]', 'How to deploy FastAPI')
    await page.click('button:has-text("Search")')

    // 로딩 상태 확인
    await expect(page.locator('text=Searching')).toBeVisible()

    // 결과 확인 (최대 30초 대기)
    await expect(page.locator('.search-result')).toBeVisible({ timeout: 30000 })

    // 결과 내용 확인
    const answer = page.locator('.answer')
    await expect(answer).toBeVisible()
    await expect(answer).not.toBeEmpty()

    // 출처 확인
    const sources = page.locator('.source-item')
    await expect(sources).toHaveCount(3)  // 3개 이상

    // 히스토리 저장 확인
    await page.goto('/history')
    await expect(page.locator('text=How to deploy FastAPI')).toBeVisible()
  })

  test('handles empty query', async ({ page }) => {
    await page.goto('/search')

    // 빈 입력으로 검색
    await page.click('button:has-text("Search")')

    // 에러 메시지 확인
    await expect(page.locator('text=Please enter a search query')).toBeVisible()
  })

  test('handles network error', async ({ page }) => {
    // 네트워크 차단
    await page.route('**/api/v1/search/query', (route) => route.abort())

    await page.goto('/search')
    await page.fill('input[placeholder*="Search"]', 'test')
    await page.click('button:has-text("Search")')

    // 에러 메시지 확인
    await expect(page.locator('text=Network error')).toBeVisible()
  })
})
```

### 3. E2E 테스트 실행

```bash
# 모든 브라우저에서 테스트
npx playwright test

# 특정 브라우저만
npx playwright test --project=chromium

# UI 모드 (디버깅)
npx playwright test --ui

# 헤드풀 모드 (브라우저 보면서)
npx playwright test --headed

# 리포트 확인
npx playwright show-report
```

---

## 성능 테스트

### 1. Locust 설정

```python
# backend/tests/performance/locustfile.py

from locust import HttpUser, task, between

class RAGPlatformUser(HttpUser):
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """로그인하여 토큰 받기"""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test@example.com",
            "password": "test123"
        })
        self.token = response.json()["access_token"]

    @task(10)
    def search_query(self):
        """검색 쿼리 (가장 빈번)"""
        self.client.post(
            "/api/v1/search/query",
            json={"query": "How to deploy FastAPI"},
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(3)
    def get_history(self):
        """검색 히스토리 조회"""
        self.client.get(
            "/api/v1/search/history",
            headers={"Authorization": f"Bearer {self.token}"}
        )

    @task(1)
    def get_document(self):
        """문서 조회"""
        self.client.get(
            "/api/v1/documents/1",
            headers={"Authorization": f"Bearer {self.token}"}
        )
```

### 2. 성능 테스트 실행

```bash
# Locust 실행 (헤드리스)
locust -f backend/tests/performance/locustfile.py \
  --headless \
  --users 100 \
  --spawn-rate 10 \
  --run-time 5m \
  --host http://localhost:8000

# 또는 스크립트 사용
cd backend
./scripts/run_load_test.sh

# 리포트 확인
open load-test-report.html
```

---

## 보안 테스트

### 1. Bandit (Python 정적 분석)

```bash
cd backend

# Bandit 실행
bandit -r app/ -f json -o bandit-report.json

# 심각도별 필터
bandit -r app/ -ll  # Low severity 이상
bandit -r app/ -lll # High severity만

# 특정 테스트 제외
bandit -r app/ -s B101,B601
```

### 2. Safety (의존성 취약점 스캔)

```bash
# Safety 실행
safety check --json > safety-report.json

# 상세 리포트
safety check --full-report

# CI/CD에서 사용
safety check --exit-code
```

### 3. OWASP ZAP (동적 분석)

```bash
# Docker로 ZAP 실행
docker run -v $(pwd):/zap/wrk:rw \
  -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap-report.html
```

---

## CI/CD 통합

### GitHub Actions

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run tests
        run: |
          cd frontend
          npm test -- --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Playwright
        run: |
          cd frontend
          npm ci
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report
```

---

## 관련 문서

- [Development Setup](./setup.md) - 개발 환경 설정
- [Coding Standards](./coding-standards.md) - 코딩 규칙 및 스타일 가이드

---

**테스트는 코드 품질의 기본입니다!** ✅
