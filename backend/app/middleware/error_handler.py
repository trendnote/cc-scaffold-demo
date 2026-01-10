"""
전역 에러 핸들러

Task 2.8: 에러 핸들링 및 Fallback

[HARD RULE] 민감 정보 마스킹:
- 스택 트레이스 숨김
- DB 연결 정보 숨김
- 내부 파일 경로 숨김
- IP 주소 숨김
- API 키 숨김
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from app.schemas.errors import ErrorResponse, ErrorDetail
import logging
import uuid
import re

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    전역 예외 핸들러

    모든 처리되지 않은 예외를 잡아서 표준화된 에러 응답으로 변환합니다.

    Args:
        request: FastAPI Request
        exc: 발생한 예외

    Returns:
        JSONResponse: 표준화된 에러 응답 (500)
    """
    request_id = str(uuid.uuid4())

    # HTTPException은 별도 처리
    if isinstance(exc, HTTPException):
        return await http_exception_handler(request, exc)

    # 로그 기록 (상세 정보 포함)
    logger.error(
        f"Unhandled exception: {type(exc).__name__}, "
        f"request_id={request_id}, "
        f"path={request.url.path}, "
        f"method={request.method}",
        exc_info=True
    )

    # [HARD RULE] 민감 정보 제거
    safe_message = sanitize_error_message(str(exc))

    error_response = ErrorResponse(
        error="InternalServerError",
        message="처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    HTTPException 핸들러

    Args:
        request: FastAPI Request
        exc: HTTPException

    Returns:
        JSONResponse: 표준화된 에러 응답
    """
    request_id = str(uuid.uuid4())

    logger.warning(
        f"HTTP exception: status={exc.status_code}, "
        f"request_id={request_id}, "
        f"detail={exc.detail}"
    )

    # detail이 dict인 경우 (이미 구조화된 응답)
    if isinstance(exc.detail, dict):
        error_response = ErrorResponse(
            error=exc.detail.get("error", "HTTPException"),
            message=exc.detail.get("message", str(exc.detail)),
            request_id=request_id
        )
    else:
        # detail이 문자열인 경우
        error_response = ErrorResponse(
            error="HTTPException",
            message=str(exc.detail),
            request_id=request_id
        )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Pydantic 검증 에러 핸들러 (422)

    Args:
        request: FastAPI Request
        exc: RequestValidationError

    Returns:
        JSONResponse: 표준화된 에러 응답 (422)
    """
    request_id = str(uuid.uuid4())

    logger.warning(
        f"Validation error: request_id={request_id}, "
        f"path={request.url.path}, "
        f"errors={exc.errors()}"
    )

    # Pydantic 에러 → ErrorDetail 변환
    details = [
        ErrorDetail(
            field=".".join(str(loc) for loc in error["loc"]),
            message=error["msg"],
            code=error["type"]
        )
        for error in exc.errors()
    ]

    error_response = ErrorResponse(
        error="ValidationError",
        message="요청 데이터 검증에 실패했습니다.",
        details=details,
        request_id=request_id
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json')
    )


def sanitize_error_message(message: str) -> str:
    """
    에러 메시지에서 민감 정보 제거

    [HARD RULE] 제거 대상:
    - 파일 경로 (예: /home/user/app/...)
    - DB 연결 문자열 (예: postgresql://user:pass@...)
    - IP 주소 (예: 192.168.1.1)
    - API 키 (예: api_key=abc123)

    Args:
        message: 원본 에러 메시지

    Returns:
        str: 민감 정보가 제거된 메시지
    """
    # DB 연결 문자열 제거 (파일 경로보다 먼저 처리)
    message = re.sub(
        r"(postgresql|mysql|mongodb)://[^@\s]+@[^\s:]+(?::\d+)?(?:/[^\s]*)?",
        r"\1://[hidden]",
        message,
        flags=re.IGNORECASE
    )

    # IP 주소 제거 (파일 경로보다 먼저 처리)
    message = re.sub(
        r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "[ip]",
        message
    )

    # API 키 패턴 제거
    message = re.sub(
        r"(api[_-]?key|token|secret)[=:]\s*[\w-]+",
        r"\1=[hidden]",
        message,
        flags=re.IGNORECASE
    )

    # 비밀번호 패턴 제거
    message = re.sub(
        r"(password|passwd|pwd)[=:]\s*[\w-]+",
        r"\1=[hidden]",
        message,
        flags=re.IGNORECASE
    )

    # 파일 경로 제거 (마지막에 처리)
    message = re.sub(
        r"/[a-zA-Z0-9_\-./]+",
        "[path]",
        message
    )

    return message
