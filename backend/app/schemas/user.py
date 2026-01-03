"""
사용자 정보 스키마

권한 기반 접근 제어를 위한 사용자 정보 및 컨텍스트 정의
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class User(BaseModel):
    """사용자 정보 스키마"""

    user_id: str = Field(..., description="사용자 고유 ID")
    access_level: int = Field(..., ge=1, le=3, description="접근 레벨 (1-3)")
    department: str = Field(..., description="부서명")
    email: Optional[str] = Field(None, description="이메일")

    @field_validator('access_level')
    @classmethod
    def validate_access_level(cls, v: int) -> int:
        """Access level은 1-3 범위"""
        if v not in [1, 2, 3]:
            raise ValueError("access_level은 1, 2, 3 중 하나여야 합니다")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_001",
                "access_level": 2,
                "department": "Engineering",
                "email": "user@example.com"
            }
        }


class UserContext:
    """
    사용자 컨텍스트 (JWT에서 추출)

    권한 기반 검색 및 접근 제어에 사용되는 사용자 정보
    """

    def __init__(self, user_id: str, access_level: int, department: str):
        """
        Args:
            user_id: 사용자 고유 ID
            access_level: 접근 레벨 (1: Public, 2: Internal, 3: Confidential)
            department: 부서명
        """
        self.user_id = user_id
        self.access_level = access_level
        self.department = department

        # 유효성 검증
        if access_level not in [1, 2, 3]:
            raise ValueError(f"Invalid access_level: {access_level}")
        if not department or not department.strip():
            raise ValueError("Department cannot be empty")

    @staticmethod
    def from_token(token: str) -> "UserContext":
        """
        JWT에서 사용자 정보 추출

        Args:
            token: JWT 토큰

        Returns:
            UserContext: 사용자 컨텍스트

        [NOTE] Task 3.x에서 실제 JWT 파싱 구현
        현재는 Mock 데이터 사용
        """
        # TODO: JWT 파싱 로직 구현 (Task 3.x)
        # 임시 Mock 데이터
        return UserContext(
            user_id="user_test",
            access_level=2,
            department="Engineering"
        )

    def __repr__(self) -> str:
        return (
            f"UserContext(user_id='{self.user_id}', "
            f"access_level={self.access_level}, "
            f"department='{self.department}')"
        )


class AccessLevel:
    """접근 레벨 상수 정의"""

    PUBLIC = 1        # 모든 사용자 접근 가능
    INTERNAL = 2      # 같은 부서만 접근 (또는 Management)
    CONFIDENTIAL = 3  # Management만 접근
