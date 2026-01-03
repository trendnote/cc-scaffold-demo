from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.schemas.search import (
    SearchQueryRequest,
    SearchQueryResponse,
    PerformanceMetrics,
    ResponseMetadata
)

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
    description="자연어 질문에 대한 답변 및 출처 반환"
)
async def search(request: SearchQueryRequest):
    """
    검색 API

    Args:
        request: 검색 요청 (query, limit, user_id, session_id)

    Returns:
        SearchQueryResponse: 답변 및 출처

    Raises:
        HTTPException 422: 검색어 유효성 검증 실패
        HTTPException 500: 서버 내부 오류
    """
    try:
        # TODO: Task 2.3-2.6에서 실제 검색 로직 구현

        # 임시 응답 (스켈레톤)
        return SearchQueryResponse(
            query_id="qry_temp_123",
            query=request.query,
            answer="검색 기능은 Task 2.3-2.6에서 구현될 예정입니다.",
            sources=[],
            performance=PerformanceMetrics(
                embedding_time_ms=0,
                search_time_ms=0,
                llm_time_ms=0,
                total_time_ms=0
            ),
            metadata=ResponseMetadata(
                is_fallback=True,
                fallback_reason="not_implemented",
                model_used="none",
                search_result_count=0
            )
        )

    except ValidationError as e:
        # Pydantic 검증 에러는 FastAPI가 자동으로 422 반환
        raise

    except Exception as e:
        # [HARD RULE] 에러 메시지에 민감 정보 포함 금지
        raise HTTPException(
            status_code=500,
            detail={
                "error": "InternalServerError",
                "message": "검색 처리 중 오류가 발생했습니다."
            }
        )
