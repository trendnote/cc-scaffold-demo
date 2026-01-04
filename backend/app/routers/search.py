from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
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
    responses={
        422: {"description": "잘못된 검색어 (유효성 검증 실패)"},
        500: {"description": "서버 내부 오류"}
    },
    summary="검색 실행",
    description="자연어 질문에 대한 답변 및 출처 반환 (Task 2.6 완성)"
)
async def search(request: SearchQueryRequest):
    """
    검색 API (Task 2.6 완성 버전)

    Args:
        request: 검색 요청 (query, limit, user_id, session_id)

    Returns:
        SearchQueryResponse: 답변, 출처, 성능 데이터

    Raises:
        HTTPException 422: 검색어 유효성 검증 실패
        HTTPException 500: 서버 내부 오류
    """
    timer = PerformanceTimer()

    try:
        logger.info(f"검색 API 요청: query='{request.query}', limit={request.limit}")

        # SearchService 초기화 및 검색 수행
        search_service = SearchService()

        # 전체 검색 수행 (성능 측정 포함)
        with timer.measure("total"):
            response = search_service.search(
                query=request.query,
                limit=request.limit,
                user=None,  # TODO: Task 3.x에서 JWT 기반 UserContext 추출
                timer=timer
            )

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
        logger.error(f"검색 API 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "InternalServerError",
                "message": "검색 처리 중 오류가 발생했습니다."
            }
        )
