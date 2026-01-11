# Task 4.1 실행 계획: 문서 자동 인덱싱 배치 스케줄러

## 📋 작업 정보
- **Task ID**: 4.1
- **Task명**: 문서 자동 인덱싱 배치 스케줄러
- **예상 시간**: 6시간
- **담당**: Backend
- **의존성**: Task 1.8 (문서 임베딩 및 Milvus 저장)
- **GitHub Issue**: #30

---

## 🎯 작업 목표

신규 문서를 자동으로 감지하고 인덱싱하는 배치 스케줄러를 구현하여 문서 관리 자동화

---

## 📐 기술 스택

- **Python**: 3.11+
- **APScheduler**: 3.10+ (작업 스케줄링)
- **FastAPI**: 0.100+ (수동 트리거 API)
- **SQLAlchemy**: 2.0+ (문서 메타데이터 관리)
- **Watchdog**: 3.0+ (파일 시스템 모니터링, 선택사항)

---

## 🏗️ 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                  Batch Scheduler System                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │  APScheduler     │──────│  File Scanner    │            │
│  │  (Cron: 2AM)     │      │  (폴더 모니터링)   │            │
│  └──────────────────┘      └──────────────────┘            │
│           │                         │                        │
│           └─────────┬───────────────┘                       │
│                     ▼                                        │
│           ┌──────────────────┐                              │
│           │  Indexing Queue  │                              │
│           │  (신규 문서 큐)    │                              │
│           └──────────────────┘                              │
│                     │                                        │
│                     ▼                                        │
│           ┌──────────────────┐                              │
│           │  Document Indexer│◄─── Task 1.8 재사용           │
│           │  (파싱 + 임베딩)   │                              │
│           └──────────────────┘                              │
│                     │                                        │
│           ┌─────────┴─────────┐                             │
│           ▼                   ▼                              │
│  ┌───────────────┐   ┌───────────────┐                     │
│  │  PostgreSQL   │   │    Milvus     │                     │
│  │  (메타데이터)   │   │   (벡터)      │                     │
│  └───────────────┘   └───────────────┘                     │
│                                                               │
│  ┌──────────────────────────────────────────┐               │
│  │  Admin API (수동 트리거)                   │               │
│  │  POST /api/v1/admin/index                │               │
│  └──────────────────────────────────────────┘               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 구현 계획

### Phase 1: APScheduler 설정 (2시간)

#### 1.1 APScheduler 설치 및 설정
**파일**: `backend/requirements.txt`
```python
apscheduler==3.10.4
```

**파일**: `backend/app/scheduler/config.py`
```python
"""
배치 스케줄러 설정
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_scheduler() -> AsyncIOScheduler:
    """
    APScheduler 인스턴스 생성

    Returns:
        AsyncIOScheduler: 설정된 스케줄러
    """
    jobstores = {
        'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
    }

    job_defaults = {
        'coalesce': True,  # 누락된 실행을 하나로 합침
        'max_instances': 1,  # 동시 실행 방지
        'misfire_grace_time': 3600  # 1시간 이내 누락 실행 허용
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        job_defaults=job_defaults,
        timezone='Asia/Seoul'
    )

    logger.info("APScheduler initialized")
    return scheduler
```

#### 1.2 스케줄러 통합
**파일**: `backend/app/main.py`
```python
from contextlib import asynccontextmanager
from app.scheduler.config import create_scheduler
from app.scheduler.jobs import register_jobs

scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행"""
    global scheduler

    # Startup
    logger.info("FastAPI 서버 시작")

    # 스케줄러 시작
    scheduler = create_scheduler()
    register_jobs(scheduler)
    scheduler.start()
    logger.info("Scheduler started")

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

    logger.info("FastAPI 서버 종료")
```

---

### Phase 2: 문서 스캔 로직 구현 (2시간)

#### 2.1 파일 스캐너
**파일**: `backend/app/scheduler/file_scanner.py`
```python
"""
문서 저장소 스캔 및 신규 문서 감지
"""
from pathlib import Path
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document
import logging

logger = logging.getLogger(__name__)


class FileScanner:
    """문서 저장소 스캐너"""

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt', '.md'}

    def __init__(self, watch_dir: str):
        """
        Args:
            watch_dir: 모니터링할 디렉토리 경로
        """
        self.watch_dir = Path(watch_dir)
        if not self.watch_dir.exists():
            raise ValueError(f"Directory not found: {watch_dir}")

    async def scan_for_new_documents(
        self,
        db: AsyncSession
    ) -> List[Dict[str, str]]:
        """
        신규 문서 스캔

        Args:
            db: DB 세션

        Returns:
            List[Dict]: 신규 문서 리스트
                - file_path: 파일 경로
                - file_name: 파일명
                - file_type: 파일 타입
        """
        new_docs = []

        # 저장소 전체 스캔
        for file_path in self.watch_dir.rglob('*'):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            # DB에 이미 존재하는지 확인
            exists = await self._check_document_exists(
                db,
                str(file_path.absolute())
            )

            if not exists:
                new_docs.append({
                    'file_path': str(file_path.absolute()),
                    'file_name': file_path.name,
                    'file_type': file_path.suffix.lower()[1:]  # .pdf -> pdf
                })

        logger.info(f"Found {len(new_docs)} new documents")
        return new_docs

    async def _check_document_exists(
        self,
        db: AsyncSession,
        file_path: str
    ) -> bool:
        """
        문서가 DB에 존재하는지 확인

        Args:
            db: DB 세션
            file_path: 파일 경로

        Returns:
            bool: 존재 여부
        """
        from sqlalchemy import select

        stmt = select(Document).where(
            Document.document_source == file_path
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None
```

#### 2.2 인덱싱 큐 관리
**파일**: `backend/app/scheduler/indexing_queue.py`
```python
"""
인덱싱 작업 큐 관리
"""
from typing import List, Dict
import asyncio
from app.services.document_indexer import DocumentIndexer
from app.db.base import get_db
import logging

logger = logging.getLogger(__name__)


class IndexingQueue:
    """인덱싱 작업 큐"""

    def __init__(self, max_concurrent: int = 5):
        """
        Args:
            max_concurrent: 최대 동시 처리 수
        """
        self.max_concurrent = max_concurrent
        self.indexer = DocumentIndexer()

    async def process_documents(
        self,
        documents: List[Dict[str, str]]
    ) -> Dict[str, int]:
        """
        문서 배치 인덱싱

        Args:
            documents: 문서 리스트

        Returns:
            Dict: 처리 결과
                - success: 성공 개수
                - failed: 실패 개수
                - total: 전체 개수
        """
        if not documents:
            return {'success': 0, 'failed': 0, 'total': 0}

        results = {
            'success': 0,
            'failed': 0,
            'total': len(documents)
        }

        # 세마포어로 동시 처리 수 제한
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def process_with_semaphore(doc: Dict[str, str]):
            async with semaphore:
                return await self._process_single_document(doc)

        # 병렬 처리
        tasks = [
            process_with_semaphore(doc)
            for doc in documents
        ]

        completed = await asyncio.gather(*tasks, return_exceptions=True)

        # 결과 집계
        for result in completed:
            if isinstance(result, Exception):
                results['failed'] += 1
                logger.error(f"Indexing failed: {result}")
            elif result:
                results['success'] += 1
            else:
                results['failed'] += 1

        logger.info(
            f"Indexing completed: {results['success']}/{results['total']} succeeded"
        )

        return results

    async def _process_single_document(
        self,
        doc: Dict[str, str]
    ) -> bool:
        """
        단일 문서 인덱싱 (재시도 포함)

        Args:
            doc: 문서 정보

        Returns:
            bool: 성공 여부
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                async for db in get_db():
                    await self.indexer.index_document(
                        db=db,
                        file_path=doc['file_path'],
                        file_name=doc['file_name'],
                        file_type=doc['file_type']
                    )
                    return True

            except Exception as e:
                retry_count += 1
                logger.warning(
                    f"Indexing retry {retry_count}/{max_retries}: {e}"
                )

                if retry_count >= max_retries:
                    logger.error(
                        f"Indexing failed after {max_retries} retries: "
                        f"{doc['file_path']}"
                    )
                    return False

                # Exponential backoff
                await asyncio.sleep(2 ** retry_count)

        return False
```

---

### Phase 3: 스케줄 작업 등록 (1시간)

#### 3.1 배치 작업 정의
**파일**: `backend/app/scheduler/jobs.py`
```python
"""
스케줄 작업 정의
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.scheduler.file_scanner import FileScanner
from app.scheduler.indexing_queue import IndexingQueue
from app.db.base import get_db
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def auto_index_new_documents():
    """
    신규 문서 자동 인덱싱 작업

    매일 새벽 2시 실행
    """
    logger.info("Starting auto-indexing job")

    try:
        scanner = FileScanner(settings.DOCUMENT_STORAGE_PATH)
        queue = IndexingQueue(max_concurrent=5)

        async for db in get_db():
            # 신규 문서 스캔
            new_docs = await scanner.scan_for_new_documents(db)

            if not new_docs:
                logger.info("No new documents found")
                return

            # 인덱싱 실행
            results = await queue.process_documents(new_docs)

            logger.info(
                f"Auto-indexing completed: "
                f"{results['success']}/{results['total']} succeeded, "
                f"{results['failed']} failed"
            )

    except Exception as e:
        logger.error(f"Auto-indexing job failed: {e}", exc_info=True)
        raise


def register_jobs(scheduler: AsyncIOScheduler):
    """
    스케줄 작업 등록

    Args:
        scheduler: APScheduler 인스턴스
    """
    # 매일 새벽 2시 자동 인덱싱
    scheduler.add_job(
        auto_index_new_documents,
        trigger=CronTrigger(hour=2, minute=0),
        id='auto_index_documents',
        name='Auto Index New Documents',
        replace_existing=True
    )

    logger.info("Jobs registered successfully")
```

---

### Phase 4: 수동 트리거 API (1시간)

#### 4.1 관리자 API 라우터
**파일**: `backend/app/routers/admin.py`
```python
"""
관리자 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from app.scheduler.file_scanner import FileScanner
from app.scheduler.indexing_queue import IndexingQueue
from app.db.base import get_db
from app.core.config import settings
from app.routers.auth import get_current_user
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


class IndexTriggerResponse(BaseModel):
    """인덱싱 트리거 응답"""
    message: str
    job_id: str


class IndexStatusResponse(BaseModel):
    """인덱싱 상태 응답"""
    status: str  # "pending", "running", "completed", "failed"
    total: int
    success: int
    failed: int
    started_at: str | None
    completed_at: str | None


async def verify_admin_user(
    user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    관리자 권한 확인

    Args:
        user: 현재 사용자

    Returns:
        Dict: 사용자 정보

    Raises:
        HTTPException 403: 관리자 권한 없음
    """
    if user.get("access_level", 0) < 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )

    return user


@router.post("/index", response_model=IndexTriggerResponse)
async def trigger_manual_indexing(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: Dict[str, Any] = Depends(verify_admin_user)
) -> IndexTriggerResponse:
    """
    수동 인덱싱 트리거

    관리자만 실행 가능

    Args:
        background_tasks: FastAPI 백그라운드 작업
        db: DB 세션
        user: 현재 사용자 (관리자)

    Returns:
        IndexTriggerResponse: 작업 ID 및 메시지
    """
    import uuid

    job_id = f"manual_index_{uuid.uuid4().hex[:8]}"

    logger.info(
        f"Manual indexing triggered: job_id={job_id}, "
        f"user={user['email']}"
    )

    # 백그라운드에서 인덱싱 실행
    background_tasks.add_task(
        run_manual_indexing,
        job_id=job_id,
        user_email=user['email']
    )

    return IndexTriggerResponse(
        message="인덱싱 작업이 시작되었습니다",
        job_id=job_id
    )


async def run_manual_indexing(job_id: str, user_email: str):
    """
    수동 인덱싱 실행 (백그라운드)

    Args:
        job_id: 작업 ID
        user_email: 사용자 이메일
    """
    try:
        logger.info(f"Starting manual indexing: job_id={job_id}")

        scanner = FileScanner(settings.DOCUMENT_STORAGE_PATH)
        queue = IndexingQueue(max_concurrent=5)

        async for db in get_db():
            new_docs = await scanner.scan_for_new_documents(db)

            if not new_docs:
                logger.info(f"No new documents: job_id={job_id}")
                return

            results = await queue.process_documents(new_docs)

            logger.info(
                f"Manual indexing completed: job_id={job_id}, "
                f"success={results['success']}, failed={results['failed']}"
            )

    except Exception as e:
        logger.error(
            f"Manual indexing failed: job_id={job_id}, error={e}",
            exc_info=True
        )
```

#### 4.2 main.py에 라우터 등록
**파일**: `backend/app/main.py`
```python
from app.routers import admin

# 라우터 등록
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
```

---

## 🧪 테스트 계획

### 단위 테스트
**파일**: `backend/tests/test_scheduler.py`
```python
import pytest
from app.scheduler.file_scanner import FileScanner
from app.scheduler.indexing_queue import IndexingQueue


class TestFileScanner:
    """파일 스캐너 테스트"""

    @pytest.mark.asyncio
    async def test_scan_new_documents(self, db_session, tmp_path):
        """신규 문서 스캔 테스트"""
        # 테스트 파일 생성
        test_file = tmp_path / "test.pdf"
        test_file.write_text("test content")

        scanner = FileScanner(str(tmp_path))
        new_docs = await scanner.scan_for_new_documents(db_session)

        assert len(new_docs) == 1
        assert new_docs[0]['file_name'] == 'test.pdf'
        assert new_docs[0]['file_type'] == 'pdf'

    @pytest.mark.asyncio
    async def test_ignore_unsupported_files(self, db_session, tmp_path):
        """미지원 파일 무시 테스트"""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("test content")

        scanner = FileScanner(str(tmp_path))
        new_docs = await scanner.scan_for_new_documents(db_session)

        assert len(new_docs) == 0


class TestIndexingQueue:
    """인덱싱 큐 테스트"""

    @pytest.mark.asyncio
    async def test_process_documents_success(self, mocker):
        """문서 처리 성공 테스트"""
        # Mock indexer
        mock_indexer = mocker.patch(
            'app.scheduler.indexing_queue.DocumentIndexer'
        )

        queue = IndexingQueue()
        docs = [
            {'file_path': '/test1.pdf', 'file_name': 'test1.pdf', 'file_type': 'pdf'}
        ]

        results = await queue.process_documents(docs)

        assert results['total'] == 1
        assert results['success'] == 1
        assert results['failed'] == 0

    @pytest.mark.asyncio
    async def test_process_documents_with_retry(self, mocker):
        """재시도 로직 테스트"""
        # First call fails, second succeeds
        mock_indexer = mocker.patch(
            'app.scheduler.indexing_queue.DocumentIndexer.index_document',
            side_effect=[Exception("Error"), None]
        )

        queue = IndexingQueue()
        doc = {'file_path': '/test.pdf', 'file_name': 'test.pdf', 'file_type': 'pdf'}

        result = await queue._process_single_document(doc)

        assert result is True
        assert mock_indexer.call_count == 2
```

### 통합 테스트
**파일**: `backend/tests/integration/test_batch_scheduler.py`
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_manual_indexing_trigger(client: AsyncClient, admin_token):
    """수동 인덱싱 트리거 테스트"""
    response = await client.post(
        "/api/v1/admin/index",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data['message'] == "인덱싱 작업이 시작되었습니다"
    assert 'job_id' in data


@pytest.mark.asyncio
async def test_manual_indexing_requires_admin(client: AsyncClient, user_token):
    """관리자 권한 필요 테스트"""
    response = await client.post(
        "/api/v1/admin/index",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 403
```

---

## ✅ 검증 기준

### 기능 검증
- [ ] APScheduler 정상 실행 (서버 시작 시)
- [ ] 신규 문서 스캔 성공 (테스트 파일 5개)
- [ ] 자동 인덱싱 스케줄 등록 확인 (새벽 2시)
- [ ] 수동 트리거 API 테스트 (POST /api/v1/admin/index)
- [ ] 관리자 권한 확인 (일반 사용자 403)

### 성능 검증
- [ ] 10개 문서 동시 인덱싱 성공
- [ ] 배치 처리 시간 측정 (10개 < 5분)
- [ ] 재시도 로직 확인 (실패 → 재시도 3회)

### 로그 검증
- [ ] 배치 시작/종료 로그 확인
- [ ] 성공/실패 개수 로그 확인
- [ ] 에러 로그 확인 (실패 시)

---

## 📂 파일 구조

```
backend/
├── app/
│   ├── scheduler/
│   │   ├── __init__.py
│   │   ├── config.py              # APScheduler 설정
│   │   ├── jobs.py                # 스케줄 작업 정의
│   │   ├── file_scanner.py        # 문서 스캔
│   │   └── indexing_queue.py      # 인덱싱 큐
│   ├── routers/
│   │   └── admin.py               # 관리자 API
│   └── main.py                     # 스케줄러 통합
├── tests/
│   ├── test_scheduler.py          # 단위 테스트
│   └── integration/
│       └── test_batch_scheduler.py # 통합 테스트
└── requirements.txt               # apscheduler 추가
```

---

## 🔒 보안 고려사항

### [HARD RULE] 준수
1. **관리자 권한 확인**
   - 수동 트리거 API는 access_level >= 3만 허용
   - JWT 토큰 검증 필수

2. **파일 경로 검증**
   - 심볼릭 링크 차단
   - 절대 경로만 허용
   - 디렉토리 트래버설 방지

3. **로그 보안**
   - 파일 경로에 민감 정보 포함 시 마스킹
   - 에러 로그에 시스템 정보 노출 금지

### 입력 검증
```python
# 파일 경로 검증
def validate_file_path(file_path: Path) -> bool:
    """
    파일 경로 안전성 검증

    Args:
        file_path: 검증할 경로

    Returns:
        bool: 안전 여부
    """
    # 심볼릭 링크 차단
    if file_path.is_symlink():
        return False

    # 절대 경로 확인
    if not file_path.is_absolute():
        return False

    # watch_dir 하위 경로인지 확인
    try:
        file_path.relative_to(WATCH_DIR)
    except ValueError:
        return False

    return True
```

---

## 🚨 에러 처리

### 재시도 전략
```python
# Exponential Backoff
retry_delays = [1, 2, 4]  # 1초, 2초, 4초

for attempt in range(3):
    try:
        await index_document(doc)
        break
    except Exception as e:
        if attempt < 2:
            await asyncio.sleep(retry_delays[attempt])
        else:
            logger.error(f"Failed after 3 retries: {doc}")
```

### 에러 분류
1. **Retriable Errors** (재시도 가능)
   - 네트워크 타임아웃
   - Milvus 연결 실패
   - DB 락

2. **Non-Retriable Errors** (재시도 불가)
   - 파일 손상
   - 파일 형식 오류
   - 권한 없음

---

## 📊 모니터링

### 배치 실행 로그
```json
{
  "timestamp": "2026-01-10T02:00:00Z",
  "job_id": "auto_index_documents",
  "status": "completed",
  "duration_seconds": 120,
  "documents_scanned": 15,
  "documents_indexed": 12,
  "documents_failed": 3,
  "success_rate": 0.8
}
```

### 알림 조건
- 성공률 < 80% → 경고
- 배치 실행 실패 → 에러
- 처리 시간 > 30분 → 경고

---

## 🔄 향후 개선 사항

### Phase 4 이후
1. **실시간 파일 모니터링**
   - Watchdog 라이브러리로 실시간 감지
   - 파일 생성 즉시 인덱싱

2. **증분 업데이트**
   - 수정된 문서 재인덱싱
   - 변경 감지 (파일 해시)

3. **배치 우선순위**
   - 중요 문서 우선 처리
   - 부서별 우선순위

4. **분산 처리**
   - Celery로 대용량 처리
   - Redis 큐

---

## 📚 참고 자료

- [APScheduler Documentation](https://apscheduler.readthedocs.io/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [Watchdog Documentation](https://python-watchdog.readthedocs.io/)

---

**작성자**: Task Planner
**작성일**: 2026-01-10
**버전**: 1.0.0
