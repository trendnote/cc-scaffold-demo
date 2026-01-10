"""
인증 관련 API 엔드포인트
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Dict, Any
from datetime import timedelta

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    verify_token,
)
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


# 요청/응답 모델
class LoginRequest(BaseModel):
    """로그인 요청"""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """로그인 응답"""

    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class LogoutResponse(BaseModel):
    """로그아웃 응답"""

    message: str


# Mock 사용자 데이터베이스
# 실제 프로덕션에서는 데이터베이스에서 조회해야 함
#
# 비밀번호 해시는 사전 계산된 값을 사용합니다 (password123)
# bcrypt 해싱은 매우 느리기 때문에 모듈 로드 시점에 실행하면 성능 문제가 발생합니다
MOCK_USERS = {
    "user@example.com": {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "user@example.com",
        "name": "일반 사용자",
        "department": "개발팀",
        "access_level": 1,
        # 비밀번호: password123 (사전 계산된 bcrypt 해시)
        "hashed_password": "$2b$12$8ECNcgJ1aPi4quRn41uM3uRejX9LZBeZlKMjm.NCjbAAjbzpsRcQK",
        "is_active": True,
    },
    "admin@example.com": {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "admin@example.com",
        "name": "관리자",
        "department": "관리팀",
        "access_level": 3,
        # 비밀번호: password123 (사전 계산된 bcrypt 해시)
        "hashed_password": "$2b$12$8ECNcgJ1aPi4quRn41uM3uRejX9LZBeZlKMjm.NCjbAAjbzpsRcQK",
        "is_active": True,
    },
}


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(request: LoginRequest) -> LoginResponse:
    """
    사용자 로그인

    Mock 인증 시스템으로 이메일/비밀번호 확인 후 JWT 토큰 발급

    Args:
        request: 로그인 요청 (email, password)

    Returns:
        LoginResponse: JWT 토큰과 사용자 정보

    Raises:
        HTTPException 401: 인증 실패
    """
    # 1. 사용자 조회
    user = MOCK_USERS.get(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
        )

    # 2. 비밀번호 검증
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
        )

    # 3. 활성 사용자 확인
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다",
        )

    # 4. JWT 토큰 생성
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        secret_key=settings.JWT_SECRET,
        expires_delta=timedelta(hours=1),
    )

    # 5. 응답 데이터 구성 (비밀번호 제외)
    user_data = {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "department": user["department"],
        "access_level": user["access_level"],
    }

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data,
    )


@router.post("/logout", response_model=LogoutResponse, status_code=status.HTTP_200_OK)
async def logout() -> LogoutResponse:
    """
    사용자 로그아웃

    클라이언트에서 토큰을 삭제하도록 응답
    실제 토큰 무효화는 클라이언트 측에서 수행

    Returns:
        LogoutResponse: 로그아웃 성공 메시지
    """
    return LogoutResponse(message="로그아웃되었습니다")


# 인증 의존성
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    현재 사용자 정보 가져오기 (JWT 토큰 검증)

    Args:
        credentials: Bearer 토큰

    Returns:
        Dict[str, Any]: 사용자 정보 (user_id, email 등)

    Raises:
        HTTPException 401: 인증 실패
    """
    token = credentials.credentials
    payload = verify_token(token, settings.JWT_SECRET)

    email = payload.get("sub")
    user_id = payload.get("user_id")

    if not email or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다",
        )

    # Mock 사용자 정보 반환 (실제로는 DB에서 조회)
    user = MOCK_USERS.get(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
        )

    return {
        "user_id": user_id,
        "email": email,
        "name": user["name"],
        "department": user["department"],
        "access_level": user["access_level"],
    }
