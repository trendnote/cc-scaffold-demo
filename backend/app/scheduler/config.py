"""
배치 스케줄러 설정
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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
    # Convert async URL to sync URL for SQLAlchemyJobStore
    sync_db_url = str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "postgresql://")

    jobstores = {
        'default': SQLAlchemyJobStore(url=sync_db_url)
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
