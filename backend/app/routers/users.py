from fastapi import APIRouter, status
from pydantic import BaseModel
from typing import List

router = APIRouter()


class SearchHistory(BaseModel):
    """검색 히스토리"""
    query_id: str
    query: str
    timestamp: str
    response_time_ms: int


@router.get(
    "/me/history",
    response_model=List[SearchHistory],
    summary="내 검색 히스토리",
    description="현재 사용자의 검색 히스토리 반환"
)
async def get_my_history(page: int = 1, page_size: int = 20):
    """
    검색 히스토리 조회 (Task 2.7에서 구현 예정)
    """
    # TODO: Task 2.7에서 구현
    return []
