from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
import uuid
import re


class SearchQueryRequest(BaseModel):
    """검색 요청 스키마"""
    query: str = Field(..., min_length=5, max_length=200, description="검색어 (5-200자)")
    limit: int = Field(default=5, ge=1, le=20, description="결과 개수 (1-20)")
    user_id: Optional[str] = Field(None, description="사용자 ID")
    session_id: Optional[str] = Field(None, description="세션 ID")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """
        검색어 유효성 검증

        [HARD RULE] 보안 검증:
        - SQL Injection 패턴 차단
        - XSS 공격 패턴 차단
        - 허용된 문자만 포함
        """
        # 1. 공백 정규화 (여러 공백 → 하나)
        v = ' '.join(v.split())

        # 2. 빈 값 검사
        if not v.strip():
            raise ValueError("검색어는 빈 값일 수 없습니다.")

        # 3. SQL Injection 패턴 검사
        sql_patterns = [
            r"(\bunion\b|\bselect\b|\bdrop\b|\bdelete\b|\binsert\b|\bupdate\b)",
            r"(--|;|\/\*|\*\/)",
            r"(\bor\b\s+\d+\s*=\s*\d+)",
            r"(\band\b\s+\d+\s*=\s*\d+)",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(
                    "검색어에 허용되지 않는 패턴이 포함되어 있습니다"
                )

        # 4. XSS 공격 패턴 검사
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onerror\s*=",
            r"onload\s*=",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("검색어에 허용되지 않는 스크립트가 포함되어 있습니다.")

        # 5. 허용된 문자만 포함 (한글, 영어, 숫자, 공백, 일부 특수문자)
        allowed_pattern = r'^[가-힣a-zA-Z0-9\s\?\.\,\!\-\(\)]+$'
        if not re.match(allowed_pattern, v):
            raise ValueError(
                "검색어는 한글, 영어, 숫자, 공백, 기본 문장부호만 포함할 수 있습니다."
            )

        return v


class DocumentSource(BaseModel):
    """문서 출처 정보"""
    document_id: str = Field(..., description="문서 ID")
    document_title: str = Field(..., description="문서 제목")
    document_source: str = Field(..., description="문서 출처")
    chunk_content: str = Field(..., description="청크 내용")
    page_number: Optional[int] = Field(None, description="페이지 번호")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="관련도 점수 (0-1)")


class PerformanceMetrics(BaseModel):
    """성능 측정 정보"""
    embedding_time_ms: int = Field(..., ge=0, description="임베딩 생성 시간 (ms)")
    search_time_ms: int = Field(..., ge=0, description="벡터 검색 시간 (ms)")
    llm_time_ms: int = Field(..., ge=0, description="LLM 답변 생성 시간 (ms)")
    total_time_ms: int = Field(..., ge=0, description="전체 처리 시간 (ms)")


class ResponseMetadata(BaseModel):
    """응답 메타데이터"""
    is_fallback: bool = Field(default=False, description="Fallback 여부")
    fallback_reason: Optional[str] = Field(None, description="Fallback 이유")
    model_used: str = Field(..., description="사용된 LLM 모델")
    search_result_count: int = Field(..., ge=0, description="검색 결과 개수")


class SearchQueryResponse(BaseModel):
    """검색 응답 스키마 (Task 2.6 완성)"""
    query_id: str = Field(
        default_factory=lambda: f"qry_{uuid.uuid4().hex[:12]}",
        description="쿼리 ID (자동 생성)"
    )
    query: str = Field(..., description="검색어")
    answer: str = Field(..., description="생성된 답변")
    sources: List[DocumentSource] = Field(default_factory=list, description="문서 출처 리스트")
    performance: PerformanceMetrics = Field(..., description="성능 측정 정보")
    metadata: ResponseMetadata = Field(..., description="응답 메타데이터")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="응답 시각")

    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "qry_20260103_001",
                "query": "연차 사용 방법",
                "answer": "연차는 입사일 기준 1년 후부터 사용 가능하며, 휴가 규정 문서에 따르면...",
                "sources": [
                    {
                        "document_id": "doc_001",
                        "document_title": "휴가 규정",
                        "document_source": "HR/policies/vacation.pdf",
                        "chunk_content": "연차는 입사일 기준 1년 후부터...",
                        "page_number": 3,
                        "relevance_score": 0.95
                    }
                ],
                "performance": {
                    "embedding_time_ms": 120,
                    "search_time_ms": 350,
                    "llm_time_ms": 2300,
                    "total_time_ms": 2800
                },
                "metadata": {
                    "is_fallback": False,
                    "fallback_reason": None,
                    "model_used": "llama3",
                    "search_result_count": 5
                },
                "timestamp": "2026-01-03T12:00:00Z"
            }
        }
