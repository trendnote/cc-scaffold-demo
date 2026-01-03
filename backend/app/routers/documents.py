from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class DocumentMetadata(BaseModel):
    """문서 메타데이터"""
    id: str
    title: str
    document_type: str
    source: str
    indexed_at: Optional[str] = None


@router.get(
    "/",
    response_model=List[DocumentMetadata],
    summary="문서 목록 조회",
    description="인덱싱된 문서 목록 반환"
)
async def list_documents(skip: int = 0, limit: int = 10):
    """
    문서 목록 조회 (Phase 3에서 구현 예정)
    """
    # TODO: Phase 3에서 구현
    return []


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata,
    summary="문서 상세 조회",
    description="특정 문서의 상세 정보 반환"
)
async def get_document(document_id: str):
    """
    문서 상세 조회 (Phase 3에서 구현 예정)
    """
    # TODO: Phase 3에서 구현
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="문서 조회 기능은 Phase 3에서 구현될 예정입니다."
    )
