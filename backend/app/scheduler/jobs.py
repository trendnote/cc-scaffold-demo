"""
스케줄 작업 정의
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.scheduler.file_scanner import FileScanner
from app.scheduler.indexing_queue import IndexingQueue
from app.db.base import AsyncSessionLocal
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

        async with AsyncSessionLocal() as db:
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
