"""
텍스트 청크 분할 로직 구현

LangChain RecursiveCharacterTextSplitter를 활용하여
파싱된 문서를 RAG 처리에 적합한 크기로 분할합니다.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.document_parser.base_parser import ParsedDocument


class TextChunk(BaseModel):
    """분할된 텍스트 청크"""

    content: str = Field(..., description="청크의 텍스트 내용")
    chunk_index: int = Field(..., ge=0, description="청크 순서 (0부터 시작)")
    document_id: Optional[str] = Field(None, description="원본 문서 ID")
    document_title: Optional[str] = Field(None, description="원본 문서 제목")
    page_number: Optional[int] = Field(None, ge=1, description="원본 페이지 번호")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "This is a sample text chunk content...",
                "chunk_index": 0,
                "document_id": "doc_12345",
                "document_title": "Sample Document",
                "page_number": 1
            }
        }


class ChunkerConfig(BaseModel):
    """청크 분할 설정"""

    chunk_size: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="청크 크기 (문자 수, 약 125 토큰)"
    )
    chunk_overlap: int = Field(
        default=50,
        ge=0,
        le=500,
        description="청크 간 겹침 크기 (문자 수)"
    )
    separators: List[str] = Field(
        default=["\n\n", "\n", ". ", " ", ""],
        description="텍스트 분할 구분자 우선순위"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "chunk_size": 500,
                "chunk_overlap": 50,
                "separators": ["\n\n", "\n", ". ", " ", ""]
            }
        }


class DocumentChunker:
    """문서 청킹 서비스

    ParsedDocument를 받아 LangChain RecursiveCharacterTextSplitter로
    텍스트를 분할하고 메타데이터를 보존합니다.
    """

    def __init__(self, config: Optional[ChunkerConfig] = None):
        """
        Args:
            config: 청크 분할 설정 (기본값: chunk_size=500, chunk_overlap=50)
        """
        self.config = config or ChunkerConfig()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk_document(self, document: ParsedDocument, document_id: Optional[str] = None) -> List[TextChunk]:
        """파싱된 문서를 청크로 분할

        Args:
            document: 파싱된 문서 객체
            document_id: 문서 식별자 (파일 경로 등)

        Returns:
            TextChunk 리스트

        Raises:
            ValueError: document가 비어있는 경우
        """
        if not document.pages:
            raise ValueError("Document content is empty")

        # 모든 페이지의 텍스트를 연결
        full_text = "\n\n".join(page.content for page in document.pages if page.content.strip())

        if not full_text.strip():
            raise ValueError("Document content is empty")

        # LangChain splitter로 텍스트 분할
        text_splits = self.splitter.split_text(full_text)

        # TextChunk 객체 생성 (메타데이터 보존)
        chunks = []
        for idx, text in enumerate(text_splits):
            chunk = TextChunk(
                content=text,
                chunk_index=idx,
                document_id=document_id or document.metadata.get("file_path"),
                document_title=document.metadata.get("title"),
                page_number=document.total_pages
            )
            chunks.append(chunk)

        return chunks

    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> List[TextChunk]:
        """순수 텍스트를 청크로 분할

        Args:
            text: 분할할 텍스트
            metadata: 청크에 추가할 메타데이터 (optional)

        Returns:
            TextChunk 리스트

        Raises:
            ValueError: text가 비어있는 경우
        """
        if not text or not text.strip():
            raise ValueError("Text is empty")

        text_splits = self.splitter.split_text(text)

        chunks = []
        for idx, chunk_text in enumerate(text_splits):
            chunk = TextChunk(
                content=chunk_text,
                chunk_index=idx,
                document_id=metadata.get("document_id") if metadata else None,
                document_title=metadata.get("title") if metadata else None,
                page_number=metadata.get("page_number") if metadata else None
            )
            chunks.append(chunk)

        return chunks

    def get_chunk_statistics(self, chunks: List[TextChunk]) -> dict:
        """청크 분할 통계 계산

        Args:
            chunks: 분석할 청크 리스트

        Returns:
            통계 정보 딕셔너리
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "total_characters": 0
            }

        chunk_sizes = [len(chunk.content) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) // len(chunks),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_characters": sum(chunk_sizes)
        }
