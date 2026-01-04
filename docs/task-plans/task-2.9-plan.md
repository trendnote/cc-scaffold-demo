# Task 2.9: 성능 최적화 및 로깅 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.9
- **Task명**: 성능 최적화 및 로깅
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
전체 검색 플로우의 성능을 최적화하고 구조화된 로깅을 구현하여 P95 < 30초 목표를 달성합니다.

### 1.2 핵심 요구사항
- **성능**: [HARD RULE] P95 < 30초 (벡터 검색 < 1초, LLM < 25초, DB < 0.5초)
- **로깅**: [HARD RULE] 개인정보 마스킹, structlog 사용
- **최적화**: DB Connection Pool, 비동기 처리
- **모니터링**: 성능 프로파일링, 병목 지점 파악

### 1.3 성공 기준
- [ ] P95 < 30초 달성
- [ ] 구조화된 로깅 (JSON 포맷)
- [ ] DB Connection Pool 설정 (pool_size=20)
- [ ] 비동기 처리 최적화
- [ ] 성능 측정 리포트 작성

### 1.4 Why This Task Matters
**프로덕션 준비**:
- **사용자 경험**: 빠른 응답 속도로 만족도 향상
- **운영 효율**: 구조화된 로그로 문제 해결 시간 단축
- **확장성**: 최적화된 리소스 사용으로 확장 가능

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 2.6 완료 확인 (성능 측정 기본 구조)
ls -la backend/app/utils/timer.py

# Structlog 설치 확인
python -c "import structlog; print(structlog.__version__)"
```

### 2.2 의존성 확인
- [x] **Task 2.6**: 성능 측정 기본 구조 완료
- [ ] **requirements.txt**: structlog, python-json-logger

---

## 3. 성능 목표

### 3.1 컴포넌트별 성능 목표

| 컴포넌트 | P95 목표 | 설명 |
|----------|----------|------|
| 쿼리 임베딩 생성 | < 500ms | Ollama nomic-embed-text |
| Milvus 벡터 검색 | < 1초 | HNSW 검색 (ef=64) |
| LLM 답변 생성 | < 25초 | Ollama llama3 또는 OpenAI |
| DB 저장 | < 500ms | PostgreSQL 쓰기 |
| **전체** | **< 30초** | End-to-End 응답 |

### 3.2 최적화 전략

```
성능 최적화 우선순위:

1. LLM 호출 최적화 (가장 느린 부분)
   - 타임아웃 30초
   - 재시도 로직 개선

2. DB Connection Pooling
   - SQLAlchemy pool_size=20
   - pool_recycle=3600

3. 비동기 처리
   - async/await 활용
   - 병렬 처리 가능한 부분 식별

4. Caching (선택적)
   - 동일 쿼리 1시간 캐싱
   - Redis 또는 메모리 캐시
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 구조화된 로깅 (90분)

#### 작업 내용
**`backend/app/utils/logger.py` 작성**:

```python
import structlog
import logging
import sys
from typing import Any, Dict


def configure_logging(log_level: str = "INFO"):
    """
    Structlog 구조화된 로깅 설정

    [HARD RULE] 개인정보 마스킹:
    - user_id: 뒤 4자리만 표시
    - email: @ 앞 2자만 표시
    - query: 민감 키워드 마스킹
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            _mask_sensitive_data,  # 커스텀 프로세서
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def _mask_sensitive_data(logger, method_name, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    개인정보 마스킹 프로세서

    [HARD RULE] 마스킹 대상:
    - user_id: user_1234 → user_****1234
    - email: user@example.com → us**@example.com
    - query: 민감 키워드 (주민번호, 계좌번호 패턴)
    """
    import re

    # user_id 마스킹
    if "user_id" in event_dict:
        user_id = event_dict["user_id"]
        if len(user_id) > 4:
            event_dict["user_id"] = f"{user_id[:-4].replace(user_id[:-4], '****')}{user_id[-4:]}"

    # email 마스킹
    if "email" in event_dict:
        email = event_dict["email"]
        if "@" in email:
            local, domain = email.split("@")
            masked_local = local[:2] + "**" if len(local) > 2 else "**"
            event_dict["email"] = f"{masked_local}@{domain}"

    # query 민감 정보 마스킹
    if "query" in event_dict:
        query = event_dict["query"]

        # 주민번호 패턴 (123456-1234567)
        query = re.sub(r"\d{6}-\d{7}", "[주민번호]", query)

        # 계좌번호 패턴 (123-456-789012)
        query = re.sub(r"\d{3}-\d{3}-\d{6,}", "[계좌번호]", query)

        # 전화번호 패턴 (010-1234-5678)
        query = re.sub(r"\d{3}-\d{4}-\d{4}", "[전화번호]", query)

        event_dict["query"] = query

    return event_dict


def get_logger(name: str):
    """
    구조화된 로거 생성

    Usage:
        logger = get_logger(__name__)
        logger.info(
            "search_request",
            user_id="user_12345",
            query="연차 사용 방법",
            response_time_ms=1234
        )
    """
    return structlog.get_logger(name)
```

---

### 4.2 Step 2: DB Connection Pool 최적화 (30분)

#### 작업 내용
**`backend/app/db/session.py` 수정**:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# DB Connection Pool 설정
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,             # 최대 20개 연결
    max_overflow=10,          # 추가 10개 overflow
    pool_recycle=3600,        # 1시간마다 연결 재생성
    pool_pre_ping=True,       # 연결 유효성 사전 확인
    echo=False                # SQL 로그 비활성화 (성능)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """DB 세션 의존성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

### 4.3 Step 3: 성능 프로파일링 (90분)

#### 작업 내용
**`backend/tests/performance/test_search_performance.py` 작성**:

```python
import time
import statistics
from app.services.search_service import SearchService
from app.utils.timer import PerformanceTimer
import pytest


@pytest.mark.performance
def test_search_performance_100_requests():
    """
    100회 검색 성능 측정

    목표:
    - P50: < 10초
    - P95: < 30초
    - P99: < 40초
    """
    search_service = SearchService()

    queries = [
        "연차 사용 방법",
        "급여 지급일",
        "회의실 예약",
        "재택근무 정책",
        "경조사 휴가"
    ] * 20  # 100개 쿼리

    total_times = []
    embedding_times = []
    search_times = []
    llm_times = []

    for query in queries:
        timer = PerformanceTimer()

        # 검색 수행
        response = search_service.search(
            query=query,
            limit=5,
            timer=timer
        )

        # 성능 데이터 수집
        total_times.append(timer.get_total())
        embedding_times.append(timer.get("embedding"))
        search_times.append(timer.get("search"))
        llm_times.append(timer.get("llm"))

    # 통계 계산
    def calculate_percentiles(data):
        p50 = statistics.median(data)
        p95 = statistics.quantiles(data, n=20)[18]  # 95th
        p99 = statistics.quantiles(data, n=100)[98]  # 99th
        return p50, p95, p99

    total_p50, total_p95, total_p99 = calculate_percentiles(total_times)
    emb_p50, emb_p95, emb_p99 = calculate_percentiles(embedding_times)
    search_p50, search_p95, search_p99 = calculate_percentiles(search_times)
    llm_p50, llm_p95, llm_p99 = calculate_percentiles(llm_times)

    # 결과 출력
    print(f"\n=== 성능 측정 결과 (100회) ===")
    print(f"Total - P50: {total_p50:.0f}ms, P95: {total_p95:.0f}ms, P99: {total_p99:.0f}ms")
    print(f"Embedding - P50: {emb_p50:.0f}ms, P95: {emb_p95:.0f}ms, P99: {emb_p99:.0f}ms")
    print(f"Search - P50: {search_p50:.0f}ms, P95: {search_p95:.0f}ms, P99: {search_p99:.0f}ms")
    print(f"LLM - P50: {llm_p50:.0f}ms, P95: {llm_p95:.0f}ms, P99: {llm_p99:.0f}ms")

    # [HARD RULE] P95 < 30초 검증
    assert total_p95 < 30000, f"P95 성능 목표 미달: {total_p95:.0f}ms"

    # 컴포넌트별 목표 검증
    assert emb_p95 < 500, f"Embedding P95 목표 미달: {emb_p95:.0f}ms"
    assert search_p95 < 1000, f"Search P95 목표 미달: {search_p95:.0f}ms"
    assert llm_p95 < 25000, f"LLM P95 목표 미달: {llm_p95:.0f}ms"
```

---

### 4.4 Step 4: 비동기 처리 최적화 (60분)

#### 작업 내용
**`backend/app/main.py` Uvicorn 설정**:

```python
# uvicorn 실행 시 workers 설정
# uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# 또는 gunicorn + uvicorn
# gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**비동기 API 엔드포인트 확인**:

```python
# backend/app/routers/search.py
@router.post("/")
async def search(request: SearchQueryRequest):
    # async/await 사용 확인
    pass
```

---

## 5. 성능 측정 리포트 작성

### 5.1 리포트 구조

**`docs/performance-report.md` 작성**:

```markdown
# 성능 측정 리포트

## 측정 환경
- CPU: [사양]
- RAM: [용량]
- OS: macOS / Linux
- Python: 3.12.3
- Ollama: llama3

## 측정 결과

| 컴포넌트 | P50 | P95 | P99 | 목표 | 달성 |
|----------|-----|-----|-----|------|------|
| 쿼리 임베딩 | 120ms | 450ms | 600ms | < 500ms | ✅ |
| 벡터 검색 | 350ms | 800ms | 1100ms | < 1초 | ✅ |
| LLM 답변 생성 | 2300ms | 23000ms | 28000ms | < 25초 | ✅ |
| 전체 | 2800ms | 24500ms | 29800ms | < 30초 | ✅ |

## 병목 지점

1. **LLM 답변 생성** (가장 느림)
   - P95: 23초
   - 최적화: OpenAI로 전환 고려

2. **벡터 검색**
   - P95: 800ms
   - 최적화: Milvus 인덱스 튜닝

## 권장 사항

1. 프로덕션 환경에서는 OpenAI GPT-4 사용 권장
2. Milvus HNSW 파라미터 튜닝 (ef 64 → 128)
3. DB Connection Pool 모니터링
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] P95 < 30초 달성
- [ ] 구조화된 로깅 (JSON 포맷)
- [ ] 개인정보 마스킹 (user_id, email, query)
- [ ] DB Connection Pool 설정 (pool_size=20)
- [ ] 비동기 처리 확인
- [ ] 성능 측정 리포트 작성

### 6.2 품질 기준

- [ ] 로그 JSON 파싱 가능
- [ ] 성능 프로파일링 결과 문서화

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/utils/logger.py` - 구조화된 로깅
2. `backend/tests/performance/test_search_performance.py` - 성능 테스트
3. `docs/performance-report.md` - 성능 측정 리포트

### 7.2 수정될 파일

1. `backend/app/db/session.py` - DB Connection Pool 설정
2. `backend/app/main.py` - Structlog 초기화
3. `backend/requirements.txt` - structlog, python-json-logger 추가

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Structlog: https://www.structlog.org/
- SQLAlchemy Pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
