from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.search import SearchQueryRequest, SearchQueryResponse
from app.services.search_service import SearchService
from app.utils.timer import PerformanceTimer
from app.db.base import get_db
from app.repositories.search_repository import SearchRepository
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=SearchQueryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"description": "잘못된 검색어 (유효성 검증 실패)"},
        500: {"description": "서버 내부 오류"}
    },
    summary="검색 실행",
    description="자연어 질문에 대한 답변 및 출처 반환 (Task 2.7: 히스토리 저장 추가)"
)
async def search(
    request: SearchQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    검색 API (Task 2.7: 히스토리 저장 추가)

    Args:
        request: 검색 요청 (query, limit, user_id, session_id)
        db: DB 세션

    Returns:
        SearchQueryResponse: 답변, 출처, 성능 데이터

    Raises:
        HTTPException 422: 검색어 유효성 검증 실패
        HTTPException 500: 서버 내부 오류
    """
    timer = PerformanceTimer()

    try:
        logger.info(f"검색 API 요청: query='{request.query}', limit={request.limit}")

        # Step 1: 쿼리 저장 (히스토리 추적)
        repository = SearchRepository(db)
        query_id = await repository.save_query(
            user_id=None,  # TODO: Task 3.x에서 JWT로 user_id 추출
            query=request.query,
            session_id=request.session_id
        )

        # Step 2: SearchService 초기화 및 검색 수행
        search_service = SearchService()

        # 전체 검색 수행 (성능 측정 포함)
        with timer.measure("total"):
            response = search_service.search(
                query=request.query,
                limit=request.limit,
                user=None,  # TODO: Task 3.x에서 JWT 기반 UserContext 추출
                timer=timer
            )

        # Step 3: 응답 저장 (실패해도 검색은 성공)
        try:
            await repository.save_response(query_id, response)
        except Exception as save_error:
            logger.error(
                f"응답 저장 실패 (검색은 성공): {save_error}",
                exc_info=True
            )
            # 응답 저장 실패해도 검색 결과는 반환

        logger.info(
            f"검색 API 완료: query_id={response.query_id}, "
            f"total_time={timer.get_total()}ms"
        )

        return response

    except ValidationError as e:
        # Pydantic 검증 에러는 FastAPI가 자동으로 422 반환
        logger.warning(f"검색 요청 검증 실패: {e}")
        raise

    except Exception as e:
        # [HARD RULE] 에러 메시지에 민감 정보 포함 금지
        logger.error(f"검색 API 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "검색 처리 중 오류가 발생했습니다."
            }
        )
