"""
통합 테스트: 전체 문서 인덱싱 파이프라인

파싱 → 청킹 → 임베딩 → 저장 전체 플로우를 검증합니다.
"""

import pytest
import tempfile
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.document_indexer import DocumentIndexer
from app.models.document import Document
from app.db.base import Base


@pytest.fixture(scope="module")
def test_db():
    """테스트용 데이터베이스 세션"""
    # PostgreSQL 연결
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/rag_platform"
    engine = create_engine(DATABASE_URL)

    # 테이블 생성 (이미 존재하면 skip)
    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = TestingSessionLocal()
    yield session
    session.close()


def test_text_file_indexing(test_db):
    """TC01: 텍스트 파일 인덱싱 전체 파이프라인"""
    # 임시 텍스트 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document. " * 100)  # 약 2500자
        temp_path = f.name

    try:
        indexer = DocumentIndexer(db_session=test_db)

        # 문서 인덱싱
        result = indexer.index_document(temp_path)

        # 검증
        assert result.success is True
        assert result.document_id is not None
        assert result.total_chunks > 0
        assert result.indexed_chunks == result.total_chunks
        assert result.processing_time_ms > 0

        # PostgreSQL 확인
        document = test_db.query(Document).filter(
            Document.id == result.document_id
        ).first()

        assert document is not None
        assert document.document_type == "TXT"
        assert document.source == temp_path

        # Cleanup
        if document:
            indexer.delete_document(str(document.id))

    finally:
        os.unlink(temp_path)


def test_empty_file_handling(test_db):
    """TC02: 빈 파일 처리"""
    # 빈 텍스트 파일 생성
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("")
        temp_path = f.name

    try:
        indexer = DocumentIndexer(db_session=test_db)

        # 문서 인덱싱
        result = indexer.index_document(temp_path)

        # 빈 파일은 실패해야 함
        assert result.success is False
        assert result.error_message is not None

    finally:
        os.unlink(temp_path)


def test_batch_indexing(test_db):
    """TC03: 배치 인덱싱"""
    # 3개의 임시 파일 생성
    temp_files = []

    try:
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Test document {i}. " * 50)
                temp_files.append(f.name)

        indexer = DocumentIndexer(db_session=test_db)

        # 배치 인덱싱
        results = indexer.index_batch(temp_files)

        # 검증
        assert len(results) == 3
        success_count = sum(1 for r in results if r.success)
        assert success_count == 3

        # Cleanup
        for result in results:
            if result.success and result.document_id:
                indexer.delete_document(result.document_id)

    finally:
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


def test_indexing_statistics(test_db):
    """TC04: 인덱싱 통계 확인"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        # 약 3000자 문서 (예상 청크 수: ~6개)
        content = "This is a test sentence for indexing. " * 100
        f.write(content)
        temp_path = f.name

    try:
        indexer = DocumentIndexer(db_session=test_db)
        result = indexer.index_document(temp_path)

        # 검증
        assert result.success is True
        assert result.total_chunks >= 5  # 최소 5개 청크
        assert result.total_chunks <= 10  # 최대 10개 청크
        assert result.indexed_chunks == result.total_chunks

        # Cleanup
        if result.document_id:
            indexer.delete_document(result.document_id)

    finally:
        os.unlink(temp_path)
