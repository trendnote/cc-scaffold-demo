# Task 2.1: FastAPI 기본 구조 및 라우터 설정 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.1
- **Task명**: FastAPI 기본 구조 및 라우터 설정
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-02
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
FastAPI 기반 REST API 서버의 기본 구조를 구축하고, 라우터, CORS, 미들웨어를 설정하여 Phase 2 개발의 기반을 마련합니다.

### 1.2 핵심 요구사항
- **기능**: FastAPI 앱 초기화, 라우터 설정, CORS, 미들웨어
- **보안**: [HARD RULE] 비밀키 환경 변수 관리, CORS 제한
- **안정성**: Health check, 타임아웃 설정
- **품질**: API 문서 자동 생성 (/docs, /redoc)

### 1.3 성공 기준
- [x] FastAPI 서버 실행 성공 (`uvicorn app.main:app`)
- [x] API 문서 접근 가능 (`/docs`, `/redoc`)
- [x] Health check 응답 (`GET /health` → 200 OK)
- [x] CORS 설정 확인 (프론트엔드 Origin 허용)
- [x] 모든 라우터 모듈 임포트 성공

### 1.4 Why This Task Matters
**Phase 2의 시작점**:
- **API 기반 마련**: 모든 검색/문서 API의 진입점
- **표준화**: 일관된 API 구조와 에러 처리
- **확장성**: 라우터 기반 모듈화로 기능 추가 용이
- **문서화**: Swagger UI로 API 명세 자동 생성

---

## 2. 선행 조건 검증

### 2.1 환경 검증
실행 전 다음 사항을 확인합니다:

```bash
# Python 버전 확인 (3.11+ 필요)
python --version

# 가상환경 활성화 확인
which python  # venv 경로여야 함

# Phase 1 완료 확인
ls -la app/services/document_indexer.py
ls -la app/services/embedding_service.py
ls -la app/models/document.py

# FastAPI 의존성 확인
python -c "import fastapi; print(fastapi.__version__)"
```

### 2.2 의존성 확인
다음 패키지들이 설치되어 있어야 합니다:

- [x] **FastAPI**: 0.109.0 이상
- [x] **Uvicorn**: 0.27.0 이상
- [x] **Pydantic**: 2.9.0 이상
- [x] **python-dotenv**: 환경 변수 관리

---

## 3. 기술 스택 선택

### 3.1 FastAPI 선택 이유

| 항목 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| **성능** | ⭐⭐⭐⭐⭐ (ASGI) | ⭐⭐⭐ (WSGI) | ⭐⭐⭐ (WSGI) |
| **타입 안전성** | ⭐⭐⭐⭐⭐ (Pydantic) | ⭐⭐ | ⭐⭐⭐ |
| **API 문서** | ⭐⭐⭐⭐⭐ (자동) | ⭐ (수동) | ⭐⭐ |
| **비동기 지원** | ⭐⭐⭐⭐⭐ (Native) | ⭐⭐ | ⭐⭐⭐ |

**최종 선택**: **FastAPI** ⭐
- 비동기 처리로 높은 처리량
- Pydantic 기반 타입 검증
- OpenAPI 자동 문서화

### 3.2 라우터 구조 설계

```
app/
├── main.py                 # FastAPI 앱 진입점
├── routers/
│   ├── __init__.py
│   ├── health.py          # Health check
│   ├── search.py          # 검색 API
│   ├── documents.py       # 문서 관리 API
│   └── users.py           # 사용자/히스토리 API
├── middleware/
│   ├── __init__.py
│   ├── logging.py         # 요청 로깅
│   └── timeout.py         # 타임아웃 처리
└── core/
    ├── __init__.py
    ├── config.py          # 설정 관리
    └── security.py        # 보안 설정
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: FastAPI 앱 초기화 (30분)

#### 작업 내용
`app/main.py` 작성:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.routers import health, search, documents, users
from app.middleware.logging import LoggingMiddleware
from app.core.config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    # Startup
    logger.info("FastAPI 서버 시작")
    yield
    # Shutdown
    logger.info("FastAPI 서버 종료")


app = FastAPI(
    title="RAG Platform API",
    description="사내 정보 검색 플랫폼 REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # 환경 변수에서 로드
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 미들웨어 추가
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(health.router, tags=["Health"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "RAG Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }
```

#### 검증
```bash
# 앱 실행
uvicorn app.main:app --reload

# 루트 접근
curl http://localhost:8000/

# API 문서 접근
open http://localhost:8000/docs
```

---

### 4.2 Step 2: 설정 관리 구현 (30min)

#### 작업 내용
`app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """환경 변수 기반 설정"""

    # 앱 설정
    APP_NAME: str = "RAG Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API 설정
    API_V1_PREFIX: str = "/api/v1"

    # CORS 설정
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js 개발 서버
        "http://localhost:8000",  # FastAPI 자체
    ]

    # 데이터베이스 설정
    DATABASE_URL: str

    # Milvus 설정
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: str = "19530"

    # Ollama 설정
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # 보안 설정 [HARD RULE]
    SECRET_KEY: str  # 필수! .env에서 로드
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 타임아웃 설정
    REQUEST_TIMEOUT_SECONDS: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

#### `.env.example` 파일 생성:
```bash
# 데이터베이스
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rag_platform

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Ollama
OLLAMA_BASE_URL=http://localhost:11434

# 보안 [HARD RULE] - 실제 .env에는 강력한 키 사용!
SECRET_KEY=your-secret-key-here-please-change-this-in-production

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

---

### 4.3 Step 3: Health Check 라우터 (20min)

#### 작업 내용
`app/routers/health.py`:

```python
from fastapi import APIRouter, status
from pydantic import BaseModel
from datetime import datetime

from app.db.milvus_client import milvus_client
from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check 응답"""
    status: str
    timestamp: datetime
    version: str
    services: dict


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="서버 및 연결된 서비스의 상태 확인"
)
async def health_check():
    """
    서버 상태 및 의존 서비스 연결 확인

    Returns:
        HealthResponse: 서버 및 서비스 상태
    """
    # Milvus 연결 확인
    milvus_health = milvus_client.health_check()

    # PostgreSQL 연결 확인 (추후 구현)
    pg_status = "healthy"  # TODO: DB 연결 확인

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        services={
            "milvus": milvus_health.get("status", "unknown"),
            "postgresql": pg_status,
        }
    )
```

#### 테스트:
```bash
curl http://localhost:8000/health
```

---

### 4.4 Step 4: Search 라우터 스켈레톤 (20min)

#### 작업 내용
`app/routers/search.py`:

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class SearchRequest(BaseModel):
    """검색 요청 스키마"""
    query: str = Field(..., min_length=5, max_length=200, description="검색어")
    limit: int = Field(default=5, ge=1, le=20, description="결과 개수")


class SearchResponse(BaseModel):
    """검색 응답 스키마"""
    query: str
    answer: str
    sources: list
    response_time_ms: int


@router.post(
    "/",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="검색 실행",
    description="자연어 질문에 대한 답변 및 출처 반환"
)
async def search(request: SearchRequest):
    """
    검색 API (Task 2.2-2.6에서 구현 예정)

    Args:
        request: 검색 요청 (query, limit)

    Returns:
        SearchResponse: 답변 및 출처
    """
    # TODO: Task 2.2-2.6에서 실제 구현
    return SearchResponse(
        query=request.query,
        answer="검색 기능은 Task 2.2-2.6에서 구현될 예정입니다.",
        sources=[],
        response_time_ms=0
    )
```

---

### 4.5 Step 5: Documents 라우터 스켈레톤 (20min)

#### 작업 내용
`app/routers/documents.py`:

```python
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class DocumentMetadata(BaseModel):
    """문서 메타데이터"""
    id: str
    title: str
    document_type: str
    source: str
    indexed_at: Optional[str] = None


@router.get(
    "/",
    response_model=List[DocumentMetadata],
    summary="문서 목록 조회",
    description="인덱싱된 문서 목록 반환"
)
async def list_documents(skip: int = 0, limit: int = 10):
    """
    문서 목록 조회 (Phase 3에서 구현 예정)
    """
    # TODO: Phase 3에서 구현
    return []


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    summary="문서 상세 조회",
    description="특정 문서의 상세 정보 반환"
)
async def get_document(document_id: str):
    """
    문서 상세 조회 (Phase 3에서 구현 예정)
    """
    # TODO: Phase 3에서 구현
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="문서 조회 기능은 Phase 3에서 구현될 예정입니다."
    )
```

---

### 4.6 Step 6: Users 라우터 스켈레톤 (20min)

#### 작업 내용
`app/routers/users.py`:

```python
from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import List

router = APIRouter()


class SearchHistory(BaseModel):
    """검색 히스토리"""
    query_id: str
    query: str
    timestamp: str
    response_time_ms: int


@router.get(
    "/me/history",
    response_model=List[SearchHistory],
    summary="내 검색 히스토리",
    description="현재 사용자의 검색 히스토리 반환"
)
async def get_my_history(page: int = 1, page_size: int = 20):
    """
    검색 히스토리 조회 (Task 2.7에서 구현 예정)
    """
    # TODO: Task 2.7에서 구현
    return []
```

---

### 4.7 Step 7: 로깅 미들웨어 (30min)

#### 작업 내용
`app/middleware/logging.py`:

```python
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next):
        """
        요청 시작/종료 로깅 및 응답 시간 측정
        """
        start_time = time.time()

        # 요청 정보 로깅
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None
            }
        )

        # 요청 처리
        response = await call_next(request)

        # 응답 시간 계산
        process_time = (time.time() - start_time) * 1000  # ms

        # 응답 정보 로깅
        logger.info(
            f"Response: {response.status_code} - {process_time:.2f}ms",
            extra={
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2)
            }
        )

        # 응답 헤더에 처리 시간 추가
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

        return response
```

---

## 5. 테스트 계획

### 5.1 단위 테스트

`tests/test_main.py`:

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    response = client.get("/")

    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_check():
    """Health check 테스트"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "services" in data


def test_api_docs_available():
    """API 문서 접근 가능 확인"""
    response = client.get("/docs")
    assert response.status_code == 200

    response = client.get("/redoc")
    assert response.status_code == 200

    response = client.get("/openapi.json")
    assert response.status_code == 200


def test_cors_headers():
    """CORS 헤더 확인"""
    response = client.options(
        "/api/v1/search/",
        headers={"Origin": "http://localhost:3000"}
    )

    assert "access-control-allow-origin" in response.headers


def test_search_skeleton():
    """검색 API 스켈레톤 테스트"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "테스트 검색어"}
    )

    assert response.status_code == 200
    assert "query" in response.json()
```

### 5.2 통합 테스트

```bash
# 서버 실행
uvicorn app.main:app --reload

# Health check
curl http://localhost:8000/health | jq

# API 문서 확인
open http://localhost:8000/docs

# 검색 API 테스트 (스켈레톤)
curl -X POST http://localhost:8000/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "테스트 검색어"}' | jq
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] FastAPI 서버 정상 실행 (`uvicorn app.main:app`)
- [ ] Health check API 응답 확인 (`GET /health` → 200 OK)
- [ ] API 문서 접근 (`/docs`, `/redoc`, `/openapi.json`)
- [ ] CORS 헤더 확인 (프론트엔드 Origin 허용)
- [ ] 모든 라우터 임포트 성공 (search, documents, users, health)
- [ ] 로깅 미들웨어 동작 확인 (X-Process-Time 헤더)
- [ ] 환경 변수 로드 확인 (.env → settings)
- [ ] SECRET_KEY 환경 변수 관리 [HARD RULE]

### 6.2 품질 기준

- [ ] Pydantic 스키마 정의 (모든 요청/응답)
- [ ] API 문서 자동 생성 (Swagger UI)
- [ ] 에러 처리 표준화 (HTTPException)
- [ ] 로그 구조화 (요청/응답 정보 포함)

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/main.py` - FastAPI 앱 진입점
2. `backend/app/core/config.py` - 설정 관리
3. `backend/app/routers/health.py` - Health check
4. `backend/app/routers/search.py` - 검색 API (스켈레톤)
5. `backend/app/routers/documents.py` - 문서 API (스켈레톤)
6. `backend/app/routers/users.py` - 사용자 API (스켈레톤)
7. `backend/app/middleware/logging.py` - 로깅 미들웨어
8. `backend/.env.example` - 환경 변수 템플릿
9. `backend/tests/test_main.py` - 메인 앱 테스트

### 7.2 수정될 파일

1. `backend/requirements.txt` - (이미 설치되어 있음)

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Architecture: `docs/architecture/architecture.md`
- FastAPI 공식 문서: https://fastapi.tiangolo.com/
- Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-02
