# Task 2.8: 에러 핸들링 및 Fallback - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.8
- **Task명**: 에러 핸들링 및 Fallback
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
모든 에러 시나리오를 처리하고 표준화된 에러 응답을 제공하며, Fallback 전략을 구현합니다.

### 1.2 핵심 요구사항
- **보안**: [HARD RULE] 에러 메시지에 민감 정보 포함 금지
- **표준화**: 일관된 에러 응답 형식
- **안정성**: 모든 에러 케이스 처리
- **Fallback**: 외부 서비스 장애 시 대안 제공

### 1.3 성공 기준
- [ ] 에러 미들웨어 구현
- [ ] 표준화된 에러 응답 스키마
- [ ] Milvus 연결 실패 시 재시도 (3회)
- [ ] LLM 타임아웃 시 검색 결과만 반환
- [ ] 에러 핸들링 테스트 10개 케이스 통과

### 1.4 Why This Task Matters
**안정적인 서비스 운영**:
- **사용자 경험**: 명확한 에러 메시지로 사용자 가이드
- **보안**: 민감 정보 노출 방지
- **장애 대응**: 외부 서비스 장애 시에도 최소 기능 유지

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 2.6 완료 확인
ls -la backend/app/routers/search.py

# FastAPI 예외 처리 확인
python -c "from fastapi import HTTPException; print('OK')"
```

### 2.2 의존성 확인
- [x] **Task 2.1**: FastAPI 기본 구조 완료
- [x] **Task 2.6**: SearchService 완료

---

## 3. 에러 카테고리 정의

### 3.1 Client Errors (4xx)

| 코드 | 이름 | 설명 | 예시 |
|------|------|------|------|
| 400 | Bad Request | 잘못된 요청 | 검색어 길이 초과 |
| 401 | Unauthorized | 인증 실패 | 잘못된 토큰 |
| 403 | Forbidden | 권한 없음 | 접근 권한 없는 문서 |
| 404 | Not Found | 리소스 없음 | 히스토리 없음 |
| 422 | Validation Error | 검증 실패 | Pydantic 검증 실패 |

### 3.2 Server Errors (5xx)

| 코드 | 이름 | 설명 | 예시 |
|------|------|------|------|
| 500 | Internal Server Error | 서버 오류 | 예상치 못한 에러 |
| 503 | Service Unavailable | 서비스 불가 | Milvus/LLM 연결 실패 |
| 504 | Gateway Timeout | 타임아웃 | LLM 30초 초과 |

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 에러 스키마 정의 (60분)

#### 작업 내용
**`backend/app/schemas/errors.py` 작성**:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    field: Optional[str] = Field(None, description="에러 발생 필드")
    message: str = Field(..., description="에러 메시지")
    code: Optional[str] = Field(None, description="에러 코드")


class ErrorResponse(BaseModel):
    """표준화된 에러 응답"""
    error: str = Field(..., description="에러 타입")
    message: str = Field(..., description="사용자 친화적 메시지")
    details: Optional[List[ErrorDetail]] = Field(None, description="상세 에러 리스트")
    request_id: Optional[str] = Field(None, description="요청 ID (디버깅용)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="에러 발생 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "검색어 검증에 실패했습니다.",
                "details": [
                    {
                        "field": "query",
                        "message": "검색어는 5-200자 이내여야 합니다.",
                        "code": "string_too_short"
                    }
                ],
                "request_id": "req_123456",
                "timestamp": "2026-01-03T12:00:00Z"
            }
        }


class ServiceUnavailableError(BaseModel):
    """서비스 불가 에러 (503)"""
    error: str = "ServiceUnavailable"
    message: str = Field(..., description="서비스 이름")
    retry_after: Optional[int] = Field(None, description="재시도 대기 시간 (초)")
```

---

### 4.2 Step 2: 에러 미들웨어 (90분)

#### 작업 내용
**`backend/app/middleware/error_handler.py` 작성**:

```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.schemas.errors import ErrorResponse, ErrorDetail
import logging
import traceback
import uuid

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    전역 예외 핸들러

    [HARD RULE] 민감 정보 마스킹:
    - 스택 트레이스 숨김
    - DB 연결 정보 숨김
    - 내부 파일 경로 숨김
    """
    request_id = str(uuid.uuid4())

    # 로그 기록 (상세 정보 포함)
    logger.error(
        f"Unhandled exception: {type(exc).__name__}, "
        f"request_id={request_id}, "
        f"path={request.url.path}",
        exc_info=True
    )

    # [HARD RULE] 민감 정보 제거
    safe_message = _sanitize_error_message(str(exc))

    error_response = ErrorResponse(
        error=type(exc).__name__,
        message="처리 중 오류가 발생했습니다.",
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Pydantic 검증 에러 핸들러 (422)

    Args:
        request: FastAPI Request
        exc: Pydantic ValidationError

    Returns:
        JSONResponse: 표준화된 에러 응답 (422)
    """
    request_id = str(uuid.uuid4())

    logger.warning(
        f"Validation error: request_id={request_id}, "
        f"errors={exc.errors()}"
    )

    # Pydantic 에러 → ErrorDetail 변환
    details = [
        ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            code=error["type"]
        )
        for error in exc.errors()
    ]

    error_response = ErrorResponse(
        error="ValidationError",
        message="요청 데이터 검증에 실패했습니다.",
        details=details,
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


def _sanitize_error_message(message: str) -> str:
    """
    에러 메시지에서 민감 정보 제거

    [HARD RULE] 제거 대상:
    - 파일 경로 (예: /home/user/app/...)
    - DB 연결 문자열 (예: postgresql://user:pass@...)
    - IP 주소
    - API 키
    """
    import re

    # 파일 경로 제거
    message = re.sub(r"(/[a-zA-Z0-9_\-./]+)+", "[path]", message)

    # DB 연결 문자열 제거
    message = re.sub(r"postgresql://[^@]+@[^/]+", "postgresql://[hidden]", message)

    # IP 주소 제거
    message = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[ip]", message)

    # API 키 패턴 제거
    message = re.sub(r"api[_-]?key[=:]\s*[\w-]+", "api_key=[hidden]", message, flags=re.IGNORECASE)

    return message
```

---

### 4.3 Step 3: Fallback 전략 (90분)

#### 작업 내용
**`backend/app/services/fallback_service.py` 작성**:

```python
import logging
from typing import List, Optional
from app.services.vector_search import SearchResult
from app.schemas.search import SearchQueryResponse, DocumentSource, PerformanceMetrics, ResponseMetadata

logger = logging.getLogger(__name__)


class FallbackService:
    """Fallback 전략 서비스"""

    @staticmethod
    def create_search_fallback(
        query: str,
        search_results: List[SearchResult],
        error_reason: str
    ) -> SearchQueryResponse:
        """
        검색 결과만 포함된 Fallback 응답 생성

        Args:
            query: 검색어
            search_results: 검색 결과
            error_reason: Fallback 이유

        Returns:
            SearchQueryResponse: Fallback 응답
        """
        logger.warning(
            f"Fallback 응답 생성: reason={error_reason}, "
            f"results={len(search_results)}"
        )

        # 검색 결과를 DocumentSource로 변환
        sources = [
            DocumentSource(
                document_id=result.document_id,
                document_title=result.metadata.get("document_title", "Unknown"),
                document_source=result.metadata.get("document_source", "Unknown"),
                chunk_content=result.content,
                page_number=result.page_number,
                relevance_score=result.relevance_score
            )
            for result in search_results
        ]

        # Fallback 답변 메시지
        fallback_answer = (
            "죄송합니다. 답변 생성에 실패했습니다. "
            "아래 검색 결과를 참고해 주세요."
        )

        return SearchQueryResponse(
            query=query,
            answer=fallback_answer,
            sources=sources,
            performance=PerformanceMetrics(
                embedding_time_ms=0,
                search_time_ms=0,
                llm_time_ms=0,
                total_time_ms=0
            ),
            metadata=ResponseMetadata(
                is_fallback=True,
                fallback_reason=error_reason,
                model_used="fallback",
                search_result_count=len(search_results)
            )
        )

    @staticmethod
    def create_error_fallback(
        query: str,
        error_message: str
    ) -> SearchQueryResponse:
        """
        에러 발생 시 빈 Fallback 응답 생성

        Args:
            query: 검색어
            error_message: 에러 메시지

        Returns:
            SearchQueryResponse: 빈 Fallback 응답
        """
        logger.error(f"에러 Fallback: message={error_message}")

        return SearchQueryResponse(
            query=query,
            answer="검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            sources=[],
            performance=PerformanceMetrics(
                embedding_time_ms=0,
                search_time_ms=0,
                llm_time_ms=0,
                total_time_ms=0
            ),
            metadata=ResponseMetadata(
                is_fallback=True,
                fallback_reason=error_message,
                model_used="error",
                search_result_count=0
            )
        )
```

---

### 4.4 Step 4: main.py 통합 (60분)

#### 작업 내용
**`backend/app/main.py` 수정**:

```python
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from app.middleware.error_handler import (
    global_exception_handler,
    validation_exception_handler
)

app = FastAPI(
    title="RAG Platform API",
    description="사내 정보 검색 플랫폼 REST API",
    version="1.0.0"
)

# 에러 핸들러 등록
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

---

## 5. 테스트 계획

### 5.1 에러 핸들링 테스트 (10개)

**`backend/tests/test_error_handling.py`**:

```python
def test_validation_error_422():
    """TC01: 검증 에러 → 422"""
    response = client.post(
        "/api/v1/search/",
        json={"query": "짧"}  # 5자 미만
    )

    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "ValidationError"


def test_milvus_unavailable_503():
    """TC02: Milvus 연결 실패 → 503"""
    # Mock: Milvus 연결 실패 시뮬레이션
    pass


def test_llm_timeout_fallback():
    """TC03: LLM 타임아웃 → Fallback"""
    # Mock: LLM 타임아웃 시뮬레이션
    pass


def test_sensitive_info_sanitization():
    """TC04: 민감 정보 마스킹"""
    message = "Error at /home/user/app/main.py with postgresql://user:pass@localhost"
    sanitized = _sanitize_error_message(message)

    assert "/home/user/app/main.py" not in sanitized
    assert "user:pass" not in sanitized
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] 에러 미들웨어 구현
- [ ] 표준화된 에러 응답 스키마
- [ ] Pydantic 검증 에러 처리 (422)
- [ ] Milvus 연결 실패 재시도 (3회)
- [ ] LLM 타임아웃 Fallback
- [ ] 민감 정보 마스킹
- [ ] 에러 핸들링 테스트 10개 통과

### 6.2 품질 기준

- [ ] 모든 에러 응답 JSON 형식 일관성
- [ ] 에러 로그 상세 기록

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/schemas/errors.py` - 에러 스키마
2. `backend/app/middleware/error_handler.py` - 에러 미들웨어
3. `backend/app/services/fallback_service.py` - Fallback 서비스
4. `backend/tests/test_error_handling.py` - 에러 핸들링 테스트 (10개)

### 7.2 수정될 파일

1. `backend/app/main.py` - 에러 핸들러 등록

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- FastAPI Error Handling: https://fastapi.tiangolo.com/tutorial/handling-errors/

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
