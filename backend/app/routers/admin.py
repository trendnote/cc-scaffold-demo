"""
관리자 API 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any
from app.scheduler.file_scanner import FileScanner
from app.scheduler.indexing_queue import IndexingQueue
from app.db.base import AsyncSessionLocal
from app.core.config import settings
from app.routers.auth import get_current_user
import logging
import uuid

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


class IndexTriggerResponse(BaseModel):
    """인덱싱 트리거 응답"""
    message: str
    job_id: str


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
    user: Dict[str, Any] = Depends(verify_admin_user)
) -> IndexTriggerResponse:
    """
    수동 인덱싱 트리거

    관리자만 실행 가능

    Args:
        background_tasks: FastAPI 백그라운드 작업
        user: 현재 사용자 (관리자)

    Returns:
        IndexTriggerResponse: 작업 ID 및 메시지
    """
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

        async with AsyncSessionLocal() as db:
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
