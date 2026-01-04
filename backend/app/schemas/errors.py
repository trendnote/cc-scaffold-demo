"""
에러 스키마 정의

Task 2.8: 에러 핸들링 및 Fallback
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    field: Optional[str] = Field(None, description="에러 발생 필드")
    message: str = Field(..., description="에러 메시지")
    code: Optional[str] = Field(None, description="에러 코드")

    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "query",
                "message": "검색어는 5-200자 이내여야 합니다.",
                "code": "string_too_short"
            }
        }
    }


class ErrorResponse(BaseModel):
    """표준화된 에러 응답"""
    error: str = Field(..., description="에러 타입 (예: ValidationError, InternalServerError)")
    message: str = Field(..., description="사용자 친화적 메시지")
    details: Optional[List[ErrorDetail]] = Field(None, description="상세 에러 리스트")
    request_id: Optional[str] = Field(None, description="요청 ID (디버깅용)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="에러 발생 시각")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ValidationError",
                "message": "검색어 검증에 실패했습니다.",
                "details": [
                    {
                        "field": "query",
                        "message": "검색어는 5-200자 이내여야 합니다.",
                        "code": "string_too_short"
                    }
                ],
                "request_id": "req_123456",
                "timestamp": "2026-01-04T10:00:00Z"
            }
        }
    }


class ServiceUnavailableError(BaseModel):
    """서비스 불가 에러 (503)"""
    error: str = "ServiceUnavailable"
    message: str = Field(..., description="서비스 이름 및 상태")
    retry_after: Optional[int] = Field(None, description="재시도 대기 시간 (초)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="에러 발생 시각")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "ServiceUnavailable",
                "message": "Milvus 서비스에 연결할 수 없습니다.",
                "retry_after": 30,
                "timestamp": "2026-01-04T10:00:00Z"
            }
        }
    }


class TimeoutError(BaseModel):
    """타임아웃 에러 (504)"""
    error: str = "GatewayTimeout"
    message: str = Field(..., description="타임아웃 발생 서비스")
    timeout_seconds: int = Field(..., description="타임아웃 시간 (초)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="에러 발생 시각")

    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "GatewayTimeout",
                "message": "LLM 응답 시간이 초과되었습니다.",
                "timeout_seconds": 30,
                "timestamp": "2026-01-04T10:00:00Z"
            }
        }
    }
