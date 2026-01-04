# Task 2.7: 검색 히스토리 저장 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.7
- **Task명**: 검색 히스토리 저장
- **예상 시간**: 3시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
PostgreSQL에 검색 쿼리와 응답을 저장하고, 사용자별 히스토리 조회 API를 구현합니다.

### 1.2 핵심 요구사항
- **기능**: 검색 쿼리/응답 저장, 히스토리 조회 API, 페이지네이션
- **데이터 보관**: 90일 (배치 삭제는 Task 4.1에서 구현)
- **성능**: 히스토리 조회 P95 < 500ms
- **안정성**: 트랜잭션 보장, DB 저장 실패 시에도 검색 성공

### 1.3 성공 기준
- [ ] 검색 쿼리 PostgreSQL 저장 성공
- [ ] 검색 응답 PostgreSQL 저장 성공
- [ ] 히스토리 조회 API 구현 (GET /api/v1/users/me/history)
- [ ] 페이지네이션 동작 (page, page_size)
- [ ] 통합 테스트 5개 케이스 통과

### 1.4 Why This Task Matters
**사용자 경험 개선**:
- **검색 기록 추적**: 사용자가 이전 검색을 다시 확인 가능
- **분석 기반**: 검색 패턴 분석으로 시스템 개선
- **컴플라이언스**: 검색 로그 보관 요구사항 충족

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 1.2 완료 확인 (search_queries, search_responses 테이블)
psql -d rag_platform -c "\d search_queries"
psql -d rag_platform -c "\d search_responses"

# Task 2.6 완료 확인 (SearchQueryResponse)
ls -la backend/app/schemas/search.py
```

### 2.2 의존성 확인
- [x] **Task 1.2**: PostgreSQL 스키마 완료 (search_queries, search_responses 테이블)
- [x] **Task 2.6**: SearchQueryResponse 스키마 완료

---

## 3. 데이터베이스 스키마 (이미 Task 1.2에서 생성됨)

### 3.1 search_queries 테이블

```sql
CREATE TABLE search_queries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    session_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_created (user_id, created_at DESC)
);
```

### 3.2 search_responses 테이블

```sql
CREATE TABLE search_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL REFERENCES search_queries(id) ON DELETE CASCADE,
    answer TEXT NOT NULL,
    sources JSONB NOT NULL,
    performance JSONB,
    metadata JSONB,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: Repository 패턴 구현 (60분)

#### 작업 내용
**`backend/app/repositories/search_repository.py` 작성**:

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.search import SearchQuery, SearchResponse
from app.schemas.search import SearchQueryResponse
import logging

logger = logging.getLogger(__name__)


class SearchRepository:
    """검색 히스토리 저장 Repository"""

    def __init__(self, db: Session):
        self.db = db

    def save_query(
        self,
        user_id: str,
        query: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        검색 쿼리 저장

        Args:
            user_id: 사용자 ID
            query: 검색어
            session_id: 세션 ID (선택적)

        Returns:
            str: 생성된 query_id (UUID)
        """
        try:
            search_query = SearchQuery(
                user_id=user_id,
                query=query,
                session_id=session_id
            )

            self.db.add(search_query)
            self.db.commit()
            self.db.refresh(search_query)

            logger.info(
                f"검색 쿼리 저장 완료: query_id={search_query.id}, "
                f"user_id={user_id}"
            )

            return str(search_query.id)

        except Exception as e:
            self.db.rollback()
            logger.error(f"검색 쿼리 저장 실패: {e}")
            raise

    def save_response(
        self,
        query_id: str,
        response: SearchQueryResponse
    ) -> None:
        """
        검색 응답 저장

        Args:
            query_id: 쿼리 ID
            response: 검색 응답 스키마
        """
        try:
            search_response = SearchResponse(
                query_id=query_id,
                answer=response.answer,
                sources=[s.model_dump() for s in response.sources],
                performance=response.performance.model_dump(),
                metadata=response.metadata.model_dump(),
                response_time_ms=response.performance.total_time_ms
            )

            self.db.add(search_response)
            self.db.commit()

            logger.info(
                f"검색 응답 저장 완료: query_id={query_id}, "
                f"response_time={response.performance.total_time_ms}ms"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"검색 응답 저장 실패: {e}")
            # [중요] 응답 저장 실패해도 검색은 성공으로 처리
            logger.warning("응답 저장 실패, 검색은 계속 진행")

    def get_user_history(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        사용자 검색 히스토리 조회 (페이지네이션)

        Args:
            user_id: 사용자 ID
            page: 페이지 번호 (1부터 시작)
            page_size: 페이지 크기

        Returns:
            dict: {
                "items": List[dict],
                "total": int,
                "page": int,
                "page_size": int,
                "total_pages": int
            }
        """
        try:
            # 전체 개수 조회
            total = self.db.query(SearchQuery).filter(
                SearchQuery.user_id == user_id
            ).count()

            # 페이지네이션 쿼리
            offset = (page - 1) * page_size

            queries = self.db.query(SearchQuery).filter(
                SearchQuery.user_id == user_id
            ).order_by(
                desc(SearchQuery.created_at)
            ).offset(offset).limit(page_size).all()

            # 응답 데이터 구성
            items = []
            for query in queries:
                # 관련 응답 조회 (LEFT JOIN)
                response = self.db.query(SearchResponse).filter(
                    SearchResponse.query_id == query.id
                ).first()

                item = {
                    "query_id": str(query.id),
                    "query": query.query,
                    "answer": response.answer if response else None,
                    "sources_count": len(response.sources) if response else 0,
                    "response_time_ms": response.response_time_ms if response else None,
                    "created_at": query.created_at.isoformat()
                }

                items.append(item)

            total_pages = (total + page_size - 1) // page_size

            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }

        except Exception as e:
            logger.error(f"히스토리 조회 실패: {e}")
            raise
```

---

### 4.2 Step 2: SQLAlchemy 모델 정의 (30분)

#### 작업 내용
**`backend/app/models/search.py` 작성**:

```python
from sqlalchemy import Column, String, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base
import uuid
from datetime import datetime


class SearchQuery(Base):
    """검색 쿼리 모델"""
    __tablename__ = "search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    query = Column(Text, nullable=False)
    session_id = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, index=True)

    # Relationship
    response = relationship("SearchResponse", back_populates="query", uselist=False)


class SearchResponse(Base):
    """검색 응답 모델"""
    __tablename__ = "search_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("search_queries.id", ondelete="CASCADE"), nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSONB, nullable=False)
    performance = Column(JSONB, nullable=True)
    metadata = Column(JSONB, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    query = relationship("SearchQuery", back_populates="response")
```

---

### 4.3 Step 3: 히스토리 조회 API (60분)

#### 작업 내용
**`backend/app/routers/users.py` 작성**:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.search_repository import SearchRepository
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me/history",
    summary="검색 히스토리 조회",
    description="현재 사용자의 검색 기록을 최신순으로 조회합니다."
)
async def get_search_history(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1-100)"),
    db: Session = Depends(get_db)
):
    """
    검색 히스토리 조회 API

    Args:
        page: 페이지 번호
        page_size: 페이지 크기
        db: DB 세션

    Returns:
        dict: 히스토리 리스트 및 페이지네이션 정보
    """
    try:
        # TODO: Task 3.x에서 JWT로 user_id 추출
        # 현재는 Mock 데이터 사용
        user_id = "user_test"

        repository = SearchRepository(db)
        result = repository.get_user_history(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        logger.info(
            f"히스토리 조회 성공: user_id={user_id}, "
            f"page={page}, total={result['total']}"
        )

        return result

    except Exception as e:
        logger.error(f"히스토리 조회 API 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "히스토리 조회 중 오류가 발생했습니다."
            }
        )
```

---

### 4.4 Step 4: Search API 통합 (30min)

#### 작업 내용
**`backend/app/routers/search.py` 수정**:

```python
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.search_repository import SearchRepository

@router.post("/")
async def search(
    request: SearchQueryRequest,
    db: Session = Depends(get_db)
):
    """검색 API (히스토리 저장 추가)"""
    timer = PerformanceTimer()

    try:
        # Step 1: 쿼리 저장
        repository = SearchRepository(db)
        query_id = repository.save_query(
            user_id=request.user_id or "anonymous",
            query=request.query,
            session_id=request.session_id
        )

        # Step 2: 검색 실행
        search_service = SearchService()
        with timer.measure("total"):
            response = search_service.search(
                query=request.query,
                limit=request.limit,
                user_id=request.user_id,
                timer=timer
            )

        # Step 3: 응답 저장 (실패해도 검색은 성공)
        try:
            repository.save_response(query_id, response)
        except Exception as e:
            logger.error(f"응답 저장 실패 (검색은 성공): {e}")

        return response

    except Exception as e:
        logger.error(f"검색 API 실패: {e}")
        raise HTTPException(status_code=500, detail="검색 실패")
```

---

## 5. 테스트 계획

### 5.1 단위 테스트

**`backend/tests/test_search_repository.py`**:

```python
def test_save_query():
    """TC01: 검색 쿼리 저장"""
    repository = SearchRepository(db_session)

    query_id = repository.save_query(
        user_id="user_001",
        query="연차 사용 방법"
    )

    assert query_id is not None


def test_get_user_history_pagination():
    """TC02: 히스토리 페이지네이션"""
    repository = SearchRepository(db_session)

    result = repository.get_user_history(
        user_id="user_001",
        page=1,
        page_size=10
    )

    assert "items" in result
    assert "total" in result
    assert "page" in result
```

### 5.2 통합 테스트

```bash
pytest backend/tests/test_search_history.py -v
# 예상: 5 passed
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] 검색 쿼리 저장 성공
- [ ] 검색 응답 저장 성공
- [ ] 히스토리 조회 API 구현
- [ ] 페이지네이션 동작 (page, page_size)
- [ ] 히스토리 조회 P95 < 500ms
- [ ] 통합 테스트 5개 케이스 통과

### 6.2 품질 기준

- [ ] DB 저장 실패 시에도 검색 성공 (resilience)
- [ ] 인덱스 최적화 (user_id, created_at)

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/models/search.py` - SQLAlchemy 모델
2. `backend/app/repositories/search_repository.py` - Repository
3. `backend/app/routers/users.py` - 히스토리 API
4. `backend/tests/test_search_repository.py` - 단위 테스트
5. `backend/tests/test_search_history.py` - 통합 테스트

### 7.2 수정될 파일

1. `backend/app/routers/search.py` - 히스토리 저장 통합

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 1.2 Plan: PostgreSQL 스키마

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
