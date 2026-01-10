"""
피드백 관련 API 엔드포인트

Task 3.8: 사용자 피드백 수집 UI
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


# 요청/응답 모델
class FeedbackRequest(BaseModel):
    """피드백 요청"""

    query_id: str = Field(..., description="검색 쿼리 ID")
    rating: int = Field(..., ge=1, le=5, description="1-5점 평가")
    comment: Optional[str] = Field(None, max_length=500, description="댓글 (선택적)")


class FeedbackResponse(BaseModel):
    """피드백 응답"""

    feedback_id: str
    message: str


@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackRequest,
    user: Dict[str, Any] = Depends(get_current_user)
) -> FeedbackResponse:
    """
    피드백 제출 API

    사용자가 검색 결과에 대해 별점(1-5) 및 댓글을 남깁니다.

    Args:
        request: 피드백 요청 (query_id, rating, comment)
        user: 현재 로그인한 사용자 정보

    Returns:
        FeedbackResponse: 피드백 ID 및 성공 메시지

    Raises:
        HTTPException 401: 인증 실패
        HTTPException 422: 유효하지 않은 입력
    """
    feedback_id = f"feedback_{uuid.uuid4().hex[:8]}"

    # TODO: DB에 저장 (추후 Task에서 구현)
    # 현재는 로그만 출력
    logger.info(
        f"Feedback received: feedback_id={feedback_id}, "
        f"query_id={request.query_id}, rating={request.rating}, "
        f"user_id={user['user_id']}, email={user['email']}, "
        f"has_comment={request.comment is not None}"
    )

    if request.comment:
        logger.info(f"Feedback comment: {request.comment[:100]}...")

    return FeedbackResponse(
        feedback_id=feedback_id,
        message="피드백이 저장되었습니다. 감사합니다!"
    )
