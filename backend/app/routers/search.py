from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class SearchRequest(BaseModel):
    """검색 요청 스키마"""
    query: str = Field(..., min_length=5, max_length=200, description="검색어")
    limit: int = Field(default=5, ge=1, le=20, description="결과 개수")


class SearchResponse(BaseModel):
    """검색 응답 스키마"""
    query: str
    answer: str
    sources: list
    response_time_ms: int


@router.post(
    "/",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="검색 실행",
    description="자연어 질문에 대한 답변 및 출처 반환"
)
async def search(request: SearchRequest):
    """
    검색 API (Task 2.2-2.6에서 구현 예정)

    Args:
        request: 검색 요청 (query, limit)

    Returns:
        SearchResponse: 답변 및 출처
    """
    # TODO: Task 2.2-2.6에서 실제 구현
    return SearchResponse(
        query=request.query,
        answer="검색 기능은 Task 2.2-2.6에서 구현될 예정입니다.",
        sources=[],
        response_time_ms=0
    )
