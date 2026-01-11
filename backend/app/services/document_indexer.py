"""
문서 인덱서 구현

파싱 → 청킹 → 임베딩 → 저장 전체 파이프라인을 오케스트레이션합니다.
"""

import logging
import os
import time
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from pymilvus import Collection

from app.services.document_parser.factory import DocumentParserFactory
from app.services.text_chunker import DocumentChunker, TextChunk
from app.services.embedding_service import OllamaEmbeddingService
from app.db.milvus_client import get_milvus_collection
from app.models.document import Document
from app.services.document_parser.base_parser import ParsedDocument

logger = logging.getLogger(__name__)


class IndexingResult(BaseModel):
    """인덱싱 결과"""

    success: bool = Field(..., description="성공 여부")
    document_id: Optional[str] = Field(None, description="문서 ID (성공 시)")
    file_path: str = Field(..., description="파일 경로")
    total_chunks: int = Field(default=0, description="생성된 청크 수")
    indexed_chunks: int = Field(default=0, description="인덱싱된 청크 수")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "file_path": "/path/to/document.pdf",
                "total_chunks": 10,
                "indexed_chunks": 10,
                "processing_time_ms": 1500
            }
        }


class DocumentIndexerConfig(BaseModel):
    """문서 인덱서 설정"""

    batch_size: int = Field(default=5, ge=1, le=20, description="배치 크기")
    max_retries: int = Field(default=3, ge=1, le=10, description="최대 재시도")
    collection_name: str = Field(
        default_factory=lambda: os.getenv("MILVUS_COLLECTION_NAME", "rag_document_chunks"),
        description="Milvus Collection명"
    )


class DocumentIndexer:
    """문서 인덱서 (파싱 → 청킹 → 임베딩 → 저장)

    전체 문서 처리 파이프라인을 오케스트레이션합니다:
    1. 문서 파싱 (PDF/DOCX/TXT/Markdown)
    2. 텍스트 청킹 (500자 단위)
    3. 임베딩 생성 (nomic-embed-text, 768차원)
    4. PostgreSQL에 메타데이터 저장
    5. Milvus에 벡터 저장
    """

    def __init__(
        self,
        db_session: Session,
        config: Optional[DocumentIndexerConfig] = None
    ):
        """
        Args:
            db_session: SQLAlchemy 세션
            config: 인덱서 설정
        """
        self.db = db_session
        self.config = config or DocumentIndexerConfig()

        # 서비스 초기화
        self.chunker = DocumentChunker()
        self.embedding_service = OllamaEmbeddingService()

        # Milvus Collection
        self.collection = get_milvus_collection(self.config.collection_name)

        logger.info(
            f"DocumentIndexer 초기화: batch_size={self.config.batch_size}, "
            f"collection={self.config.collection_name}"
        )

    def index_document(self, file_path: str) -> IndexingResult:
        """
        단일 문서 인덱싱 (전체 파이프라인)

        Args:
            file_path: 문서 파일 경로

        Returns:
            IndexingResult: 인덱싱 결과
        """
        start_time = time.time()

        logger.info(f"문서 인덱싱 시작: {file_path}")

        try:
            # Step 1: 문서 파싱
            parser = DocumentParserFactory.get_parser(file_path)
            parsed_doc = parser.parse(file_path)

            logger.info(
                f"파싱 완료: {parsed_doc.total_pages}페이지, "
                f"{parsed_doc.total_characters}자"
            )

            # Step 2: 청킹
            chunks = self.chunker.chunk_document(parsed_doc, document_id=file_path)

            logger.info(f"청킹 완료: {len(chunks)}개 청크")

            if not chunks:
                raise ValueError("청크가 생성되지 않았습니다 (빈 문서)")

            # Step 3: PostgreSQL에 문서 메타데이터 저장
            document = self._save_document_metadata(file_path, parsed_doc, len(chunks))

            logger.info(f"문서 메타데이터 저장 완료: document_id={document.id}")

            # Step 4: 임베딩 생성
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.embed_batch(chunk_texts)

            logger.info(f"임베딩 생성 완료: {len(embeddings)}개")

            # Step 5: Milvus에 저장
            indexed_count = self._save_to_milvus(
                document_id=str(document.id),
                chunks=chunks,
                embeddings=embeddings
            )

            logger.info(f"Milvus 저장 완료: {indexed_count}개 청크")

            # Step 6: 커밋
            self.db.commit()

            # 결과 반환
            processing_time_ms = int((time.time() - start_time) * 1000)

            return IndexingResult(
                success=True,
                document_id=str(document.id),
                file_path=file_path,
                total_chunks=len(chunks),
                indexed_chunks=indexed_count,
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            logger.error(f"문서 인덱싱 실패: {e}", exc_info=True)
            self.db.rollback()

            processing_time_ms = int((time.time() - start_time) * 1000)

            return IndexingResult(
                success=False,
                file_path=file_path,
                error_message=str(e),
                processing_time_ms=processing_time_ms
            )

    def index_batch(self, file_paths: List[str]) -> List[IndexingResult]:
        """
        배치 문서 인덱싱

        Args:
            file_paths: 파일 경로 리스트

        Returns:
            List[IndexingResult]: 인덱싱 결과 리스트
        """
        logger.info(f"배치 인덱싱 시작: {len(file_paths)}개 문서")

        results = []

        # 배치 크기로 분할
        for i in range(0, len(file_paths), self.config.batch_size):
            batch = file_paths[i:i + self.config.batch_size]

            logger.info(
                f"배치 {i // self.config.batch_size + 1} 처리 중 "
                f"({len(batch)}개 문서)..."
            )

            for file_path in batch:
                result = self.index_document(file_path)
                results.append(result)

        # 통계
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        logger.info(
            f"배치 인덱싱 완료: 성공 {success_count}, 실패 {fail_count}"
        )

        return results

    def _save_document_metadata(
        self,
        file_path: str,
        parsed_doc: ParsedDocument,
        chunk_count: int
    ) -> Document:
        """
        PostgreSQL에 문서 메타데이터 저장

        Args:
            file_path: 파일 경로
            parsed_doc: 파싱된 문서
            chunk_count: 생성된 청크 수

        Returns:
            Document: SQLAlchemy 모델
        """
        # 전체 문서 내용 구성 (모든 페이지 연결)
        full_content = "\n\n".join(
            page.content for page in parsed_doc.pages if page.content.strip()
        )

        # 문서 타입 추출 (확장자 기반)
        file_type = Path(file_path).suffix.upper().replace(".", "")
        if file_type == "MD":
            file_type = "MARKDOWN"

        # 메타데이터 구성
        doc_metadata = {
            "page_count": parsed_doc.total_pages,
            "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "chunk_count": chunk_count,
            "indexed_at": datetime.utcnow().isoformat(),
            **parsed_doc.metadata  # 파서에서 추출한 추가 메타데이터
        }

        document = Document(
            title=parsed_doc.metadata.get("title") or Path(file_path).stem,
            content=full_content,
            document_type=file_type,
            source=file_path,
            access_level=1,  # 기본값: Public
            department=None,  # 필요시 추가
            doc_metadata=doc_metadata
        )

        self.db.add(document)
        self.db.flush()  # ID 생성 (commit 전)

        return document

    def _save_to_milvus(
        self,
        document_id: str,
        chunks: List[TextChunk],
        embeddings: List[List[float]]
    ) -> int:
        """
        Milvus에 벡터 + 메타데이터 저장

        Args:
            document_id: 문서 ID (UUID 문자열)
            chunks: TextChunk 리스트
            embeddings: 임베딩 벡터 리스트

        Returns:
            int: 저장된 청크 수

        Raises:
            Exception: Milvus 저장 실패
        """
        if len(chunks) != len(embeddings):
            raise ValueError(
                f"청크 수({len(chunks)})와 임베딩 수({len(embeddings)})가 일치하지 않습니다"
            )

        try:
            # Collection에 맞는 형식으로 데이터 구성
            # Schema: document_id, content, embedding, chunk_index, metadata
            insert_data = [
                [document_id] * len(chunks),  # document_id (repeated)
                [chunk.content for chunk in chunks],  # content
                embeddings,                    # embedding (List[List[float]])
                list(range(len(chunks))),      # chunk_index
                [{
                    "document_title": chunk.document_title or "",
                    "chunk_length": len(chunk.content),
                    "total_chunks": len(chunks),
                    "page_number": chunk.page_number or 1
                } for chunk in chunks]  # metadata
            ]

            # Milvus에 삽입
            self.collection.insert(insert_data)
            self.collection.flush()

            logger.info(f"Milvus에 {len(chunks)}개 엔티티 저장 완료")

            return len(chunks)

        except Exception as e:
            logger.error(f"Milvus 저장 실패: {e}")
            raise

    def delete_document(self, document_id: str) -> bool:
        """
        문서 삭제 (PostgreSQL + Milvus)

        Args:
            document_id: 문서 ID (UUID 문자열)

        Returns:
            bool: 성공 여부
        """
        try:
            # Step 1: Milvus에서 삭제
            expr = f'document_id == "{document_id}"'
            self.collection.delete(expr)
            self.collection.flush()

            logger.info(f"Milvus에서 document_id={document_id} 삭제 완료")

            # Step 2: PostgreSQL에서 삭제
            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()

            if document:
                self.db.delete(document)
                self.db.commit()

                logger.info(f"PostgreSQL에서 document_id={document_id} 삭제 완료")

            return True

        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            self.db.rollback()
            return False
