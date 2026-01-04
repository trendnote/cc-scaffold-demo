"""
사용자 관련 API 라우터

Task 2.7: 검색 히스토리 조회
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.repositories.search_repository import SearchRepository
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/me/history",
    status_code=status.HTTP_200_OK,
    responses={
        500: {"description": "서버 내부 오류"}
    },
    summary="검색 히스토리 조회",
    description="현재 사용자의 검색 기록을 최신순으로 조회합니다 (Task 2.7 완성)"
)
async def get_my_history(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기 (1-100)"),
    db: AsyncSession = Depends(get_db)
):
    """
    검색 히스토리 조회 API

    Args:
        page: 페이지 번호 (1부터 시작)
        page_size: 페이지 크기 (1-100)
        db: DB 세션

    Returns:
        dict: {
            "items": List[dict],  # 검색 기록 리스트
            "total": int,  # 전체 개수
            "page": int,  # 현재 페이지
            "page_size": int,  # 페이지 크기
            "total_pages": int  # 전체 페이지 수
        }

    Raises:
        HTTPException 500: 히스토리 조회 실패
    """
    try:
        # TODO: Task 3.x에서 JWT로 user_id 추출
        # 현재는 Mock UUID 사용 (테스트용 고정 UUID)
        user_id = UUID("00000000-0000-0000-0000-000000000001")

        logger.info(
            f"히스토리 조회 API 요청: user_id={user_id}, "
            f"page={page}, page_size={page_size}"
        )

        repository = SearchRepository(db)
        result = await repository.get_user_history(
            user_id=user_id,
            page=page,
            page_size=page_size
        )

        logger.info(
            f"히스토리 조회 완료: user_id={user_id}, "
            f"page={page}, total={result['total']}, items={len(result['items'])}"
        )

        return result

    except Exception as e:
        logger.error(f"히스토리 조회 API 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "히스토리 조회 중 오류가 발생했습니다."
            }
        )
