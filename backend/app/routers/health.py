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
