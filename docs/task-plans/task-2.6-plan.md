# Task 2.6: 출처 추적 및 응답 구성 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.6
- **Task명**: 출처 추적 및 응답 구성
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
검색된 문서 정보를 추출하여 구조화된 API 응답을 생성하고, 성능 측정 데이터를 포함합니다.

### 1.2 핵심 요구사항
- **기능**: DocumentSource 스키마 완성, 응답 시간 측정
- **품질**: JSON 스키마 검증 100% 통과
- **성능**: 컴포넌트별 성능 추적 (임베딩, 검색, LLM 각각 측정)
- **안정성**: 응답 형식 일관성 보장

### 1.3 성공 기준
- [ ] DocumentSource 스키마 완성
- [ ] SearchQueryResponse 스키마 완성
- [ ] 응답 시간 측정 (embedding_time, search_time, llm_time, total_time)
- [ ] JSON 직렬화 성공
- [ ] 통합 테스트 5개 케이스 통과

### 1.4 Why This Task Matters
**사용자 신뢰 구축**:
- **투명성**: 출처를 명확히 제공하여 신뢰 향상
- **성능 가시성**: 응답 시간 측정으로 병목 지점 파악
- **API 품질**: 일관된 응답 형식으로 클라이언트 통합 용이

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 2.2 완료 확인 (스키마 기본 구조)
ls -la backend/app/schemas/search.py

# Task 2.3, 2.5a, 2.5b 완료 확인
ls -la backend/app/services/vector_search.py
ls -la backend/app/services/rag_service.py
```

### 2.2 의존성 확인
- [x] **Task 2.2**: 기본 스키마 정의 완료
- [x] **Task 2.3**: VectorSearchService 완료
- [x] **Task 2.5a/b**: RAGService 완료

---

## 3. 응답 구조 설계

### 3.1 최종 API 응답 형식

```json
{
  "query_id": "qry_20260103_001",
  "query": "연차 사용 방법",
  "answer": "휴가 규정 문서에 따르면 연차는 입사일 기준 1년 후부터 사용 가능합니다...",
  "sources": [
    {
      "document_id": "doc_001",
      "document_title": "휴가 규정",
      "document_source": "docs/leave-policy.pdf",
      "chunk_content": "연차 휴가는 입사일 기준...",
      "page_number": 3,
      "relevance_score": 0.92
    }
  ],
  "performance": {
    "embedding_time_ms": 120,
    "search_time_ms": 450,
    "llm_time_ms": 2300,
    "total_time_ms": 2870
  },
  "metadata": {
    "is_fallback": false,
    "fallback_reason": null,
    "model_used": "ollama/llama3"
  },
  "timestamp": "2026-01-03T12:00:00Z"
}
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 스키마 완성 (90분)

#### 작업 내용
**`backend/app/schemas/search.py` 완성**:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


class DocumentSource(BaseModel):
    """문서 출처 정보"""
    document_id: str = Field(..., description="문서 ID")
    document_title: str = Field(..., description="문서 제목")
    document_source: str = Field(..., description="문서 출처 (URL 또는 파일명)")
    chunk_content: str = Field(..., description="관련 청크 내용")
    page_number: Optional[int] = Field(None, description="페이지 번호")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="관련도 점수 (0-1)")


class PerformanceMetrics(BaseModel):
    """성능 측정 데이터"""
    embedding_time_ms: int = Field(..., ge=0, description="임베딩 생성 시간 (밀리초)")
    search_time_ms: int = Field(..., ge=0, description="벡터 검색 시간 (밀리초)")
    llm_time_ms: int = Field(..., ge=0, description="LLM 답변 생성 시간 (밀리초)")
    total_time_ms: int = Field(..., ge=0, description="전체 응답 시간 (밀리초)")


class ResponseMetadata(BaseModel):
    """응답 메타데이터"""
    is_fallback: bool = Field(default=False, description="Fallback 여부")
    fallback_reason: Optional[str] = Field(None, description="Fallback 이유")
    model_used: str = Field(..., description="사용된 LLM 모델")
    search_result_count: int = Field(..., ge=0, description="검색 결과 개수")


class SearchQueryResponse(BaseModel):
    """검색 응답 스키마 (완성 버전)"""
    query_id: str = Field(
        default_factory=lambda: f"qry_{uuid.uuid4().hex[:12]}",
        description="검색 쿼리 ID"
    )
    query: str = Field(..., description="원본 검색어")
    answer: str = Field(..., description="생성된 답변")
    sources: List[DocumentSource] = Field(
        default_factory=list,
        description="출처 문서 리스트"
    )
    performance: PerformanceMetrics = Field(..., description="성능 측정 데이터")
    metadata: ResponseMetadata = Field(..., description="응답 메타데이터")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="응답 생성 시각"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "qry_20260103_001",
                "query": "연차 사용 방법",
                "answer": "휴가 규정 문서에 따르면...",
                "sources": [
                    {
                        "document_id": "doc_001",
                        "document_title": "휴가 규정",
                        "document_source": "docs/leave-policy.pdf",
                        "chunk_content": "연차 휴가는...",
                        "page_number": 3,
                        "relevance_score": 0.92
                    }
                ],
                "performance": {
                    "embedding_time_ms": 120,
                    "search_time_ms": 450,
                    "llm_time_ms": 2300,
                    "total_time_ms": 2870
                },
                "metadata": {
                    "is_fallback": False,
                    "fallback_reason": None,
                    "model_used": "ollama/llama3",
                    "search_result_count": 5
                },
                "timestamp": "2026-01-03T12:00:00Z"
            }
        }
```

---

### 4.2 Step 2: 응답 빌더 서비스 (60분)

#### 작업 내용
**`backend/app/services/response_builder.py` 작성**:

```python
from typing import List
from app.schemas.search import (
    SearchQueryResponse,
    DocumentSource,
    PerformanceMetrics,
    ResponseMetadata
)
from app.services.vector_search import SearchResult
import logging

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """API 응답 구성 서비스"""

    @staticmethod
    def build_search_response(
        query: str,
        answer: str,
        search_results: List[SearchResult],
        performance: dict,
        is_fallback: bool = False,
        fallback_reason: Optional[str] = None,
        model_used: str = "ollama/llama3"
    ) -> SearchQueryResponse:
        """
        구조화된 검색 응답 생성

        Args:
            query: 검색어
            answer: 생성된 답변
            search_results: 검색 결과 리스트
            performance: 성능 측정 데이터 dict
            is_fallback: Fallback 여부
            fallback_reason: Fallback 이유
            model_used: 사용된 LLM 모델

        Returns:
            SearchQueryResponse: 구조화된 응답
        """
        logger.info(
            f"응답 구성 시작: query='{query}', "
            f"sources={len(search_results)}, "
            f"is_fallback={is_fallback}"
        )

        # DocumentSource 변환
        sources = [
            ResponseBuilder._to_document_source(result)
            for result in search_results
        ]

        # PerformanceMetrics 생성
        perf_metrics = PerformanceMetrics(
            embedding_time_ms=performance.get("embedding_time_ms", 0),
            search_time_ms=performance.get("search_time_ms", 0),
            llm_time_ms=performance.get("llm_time_ms", 0),
            total_time_ms=performance.get("total_time_ms", 0)
        )

        # ResponseMetadata 생성
        metadata = ResponseMetadata(
            is_fallback=is_fallback,
            fallback_reason=fallback_reason,
            model_used=model_used,
            search_result_count=len(search_results)
        )

        # SearchQueryResponse 생성
        response = SearchQueryResponse(
            query=query,
            answer=answer,
            sources=sources,
            performance=perf_metrics,
            metadata=metadata
        )

        logger.info(
            f"응답 구성 완료: query_id={response.query_id}, "
            f"total_time={perf_metrics.total_time_ms}ms"
        )

        return response

    @staticmethod
    def _to_document_source(result: SearchResult) -> DocumentSource:
        """
        SearchResult → DocumentSource 변환

        Args:
            result: 검색 결과

        Returns:
            DocumentSource: 문서 출처 정보
        """
        return DocumentSource(
            document_id=result.document_id,
            document_title=result.metadata.get("document_title", "Unknown"),
            document_source=result.metadata.get("document_source", "Unknown"),
            chunk_content=result.content,
            page_number=result.page_number,
            relevance_score=result.relevance_score
        )
```

---

### 4.3 Step 3: 성능 측정 유틸리티 (60분)

#### 작업 내용
**`backend/app/utils/timer.py` 작성**:

```python
import time
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """성능 측정 타이머"""

    def __init__(self):
        self.timings = {}

    @contextmanager
    def measure(self, operation: str):
        """
        컨텍스트 매니저로 성능 측정

        Usage:
            timer = PerformanceTimer()
            with timer.measure("embedding"):
                # 임베딩 생성 코드
                pass
            elapsed_ms = timer.get("embedding")
        """
        start_time = time.time()

        try:
            yield
        finally:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.timings[operation] = elapsed_ms
            logger.debug(f"{operation}: {elapsed_ms}ms")

    def get(self, operation: str) -> int:
        """
        특정 작업의 소요 시간 조회 (밀리초)

        Args:
            operation: 작업명

        Returns:
            int: 소요 시간 (밀리초)
        """
        return self.timings.get(operation, 0)

    def get_all(self) -> dict:
        """모든 성능 측정 데이터 조회"""
        return self.timings.copy()

    def get_total(self) -> int:
        """전체 소요 시간 (밀리초)"""
        return sum(self.timings.values())
```

---

### 4.4 Step 4: Search API 완성 (60분)

#### 작업 내용
**`backend/app/routers/search.py` 완성**:

```python
from fastapi import APIRouter, HTTPException, status
from app.schemas.search import SearchQueryRequest, SearchQueryResponse
from app.services.search_service import SearchService
from app.utils.timer import PerformanceTimer
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=SearchQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="검색 실행",
    description="자연어 질문에 대한 답변 및 출처 반환"
)
async def search(request: SearchQueryRequest):
    """
    검색 API (Task 2.6 완성 버전)

    Args:
        request: 검색 요청 (query, limit)

    Returns:
        SearchQueryResponse: 답변, 출처, 성능 데이터
    """
    timer = PerformanceTimer()

    try:
        # SearchService 초기화
        search_service = SearchService()

        # 전체 검색 수행 (성능 측정 포함)
        with timer.measure("total"):
            response = search_service.search(
                query=request.query,
                limit=request.limit,
                user_id=request.user_id,
                timer=timer
            )

        logger.info(
            f"검색 완료: query='{request.query}', "
            f"total_time={timer.get_total()}ms"
        )

        return response

    except Exception as e:
        logger.error(f"검색 API 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "검색 처리 중 오류가 발생했습니다."
            }
        )
```

**`backend/app/services/search_service.py` 완성**:

```python
from app.services.vector_search import VectorSearchService
from app.services.rag_service import RAGService
from app.services.response_builder import ResponseBuilder
from app.utils.timer import PerformanceTimer


class SearchService:
    """통합 검색 서비스 (Task 2.6 완성 버전)"""

    def __init__(self):
        self.vector_search = VectorSearchService()
        self.rag_service = RAGService()

    def search(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[str] = None,
        timer: Optional[PerformanceTimer] = None
    ) -> SearchQueryResponse:
        """
        전체 검색 플로우 (벡터 검색 + RAG 답변 생성)

        Args:
            query: 검색어
            limit: 최대 결과 수
            user_id: 사용자 ID
            timer: 성능 측정 타이머

        Returns:
            SearchQueryResponse: 구조화된 응답
        """
        if timer is None:
            timer = PerformanceTimer()

        # Step 1: 쿼리 임베딩 + 벡터 검색
        with timer.measure("embedding"):
            query_embedding = self.vector_search.embedding_service.embed_query(query)

        with timer.measure("search"):
            search_results = self.vector_search.search(query, top_k=limit)

        # Step 2: RAG 답변 생성
        with timer.measure("llm"):
            rag_result = self.rag_service.generate_answer_with_fallback(
                query, search_results
            )

        # Step 3: 응답 구성
        response = ResponseBuilder.build_search_response(
            query=query,
            answer=rag_result["answer"],
            search_results=search_results,
            performance={
                "embedding_time_ms": timer.get("embedding"),
                "search_time_ms": timer.get("search"),
                "llm_time_ms": timer.get("llm"),
                "total_time_ms": timer.get_total()
            },
            is_fallback=rag_result["is_fallback"],
            fallback_reason=rag_result["fallback_reason"],
            model_used=self.rag_service.provider_type
        )

        return response
```

---

## 5. 테스트 계획

### 5.1 스키마 검증 테스트

```python
def test_search_response_schema_validation():
    """TC01: SearchQueryResponse 스키마 검증"""
    response = SearchQueryResponse(
        query="연차 사용 방법",
        answer="답변...",
        sources=[],
        performance=PerformanceMetrics(
            embedding_time_ms=100,
            search_time_ms=400,
            llm_time_ms=2000,
            total_time_ms=2500
        ),
        metadata=ResponseMetadata(
            is_fallback=False,
            model_used="ollama/llama3",
            search_result_count=0
        )
    )

    # JSON 직렬화 테스트
    json_data = response.model_dump_json()
    assert "query_id" in json_data
```

### 5.2 통합 테스트

```bash
pytest backend/tests/integration/test_search_response.py -v
# 예상: 5 passed
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] DocumentSource 스키마 완성
- [ ] SearchQueryResponse 스키마 완성
- [ ] 성능 측정 (embedding, search, llm, total)
- [ ] JSON 직렬화 성공
- [ ] 통합 테스트 5개 케이스 통과

### 6.2 품질 기준

- [ ] OpenAPI 문서 자동 생성 확인
- [ ] 스키마 검증 100% 통과

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/services/response_builder.py` - 응답 구성 서비스
2. `backend/app/utils/timer.py` - 성능 측정 유틸리티
3. `backend/tests/integration/test_search_response.py` - 통합 테스트

### 7.2 수정될 파일

1. `backend/app/schemas/search.py` - 스키마 완성
2. `backend/app/routers/search.py` - API 완성
3. `backend/app/services/search_service.py` - 검색 서비스 완성

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 2.2 Plan: `docs/task-plans/task-2.2-plan.md`

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
