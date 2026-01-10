"""
JWT 토큰 생성 및 검증
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 설정 (환경 변수에서 로드)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1  # 1시간


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱

    Args:
        password: 평문 비밀번호

    Returns:
        str: 해싱된 비밀번호
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증

    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해싱된 비밀번호

    Returns:
        bool: 비밀번호 일치 여부
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    JWT Access Token 생성

    Args:
        data: 토큰에 포함할 데이터 (예: {"sub": "user_email"})
        secret_key: JWT 서명에 사용할 비밀 키
        expires_delta: 토큰 만료 시간 (None이면 기본 1시간)

    Returns:
        str: JWT 토큰
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token: str, secret_key: str) -> Dict[str, Any]:
    """
    JWT 토큰 검증 및 디코딩

    Args:
        token: JWT 토큰
        secret_key: JWT 서명 검증에 사용할 비밀 키

    Returns:
        Dict[str, Any]: 디코딩된 페이로드

    Raises:
        HTTPException: 토큰이 유효하지 않을 경우
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")

        if email is None:
            raise credentials_exception

        return payload

    except JWTError:
        raise credentials_exception
