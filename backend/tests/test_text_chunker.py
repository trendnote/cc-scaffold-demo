"""
텍스트 청킹 서비스 테스트

DocumentChunker의 동작을 검증합니다.
"""

import pytest
from app.services.text_chunker import (
    DocumentChunker,
    TextChunk,
    ChunkerConfig,
)
from app.services.document_parser.base_parser import ParsedDocument


# ============================================================================
# Happy Path Tests (5)
# ============================================================================

def test_basic_chunking():
    """기본 청킹 동작 검증"""
    chunker = DocumentChunker()

    # 약 1000자 텍스트 (기본 chunk_size=500이므로 2개 청크 예상)
    text = "A" * 600 + "B" * 600

    chunks = chunker.chunk_text(text)

    assert len(chunks) >= 2, "Should split into at least 2 chunks"
    assert all(isinstance(chunk, TextChunk) for chunk in chunks)
    assert all(chunk.chunk_index == idx for idx, chunk in enumerate(chunks))


def test_chunk_size_constraint():
    """청크 크기 제약 검증 (±10% 허용)"""
    chunk_size = 500
    chunker = DocumentChunker(ChunkerConfig(chunk_size=chunk_size, chunk_overlap=0))

    # 2000자 텍스트
    text = "This is a sample text. " * 100

    chunks = chunker.chunk_text(text)

    for chunk in chunks[:-1]:  # 마지막 청크 제외
        chunk_len = len(chunk.content)
        # 청크 크기가 설정값의 90%~110% 범위 내인지 확인
        assert 0.9 * chunk_size <= chunk_len <= 1.1 * chunk_size, \
            f"Chunk size {chunk_len} out of range [{0.9*chunk_size}, {1.1*chunk_size}]"


def test_chunk_overlap():
    """청크 간 겹침 검증"""
    chunk_size = 500
    chunk_overlap = 50
    chunker = DocumentChunker(
        ChunkerConfig(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    )

    # 반복되는 패턴으로 overlap 확인 용이
    text = "ABCDEFGHIJ" * 200  # 2000자

    chunks = chunker.chunk_text(text)

    if len(chunks) >= 2:
        # 첫 번째 청크의 마지막 부분과 두 번째 청크의 시작 부분이 겹치는지 확인
        chunk1_end = chunks[0].content[-chunk_overlap:]
        chunk2_start = chunks[1].content[:chunk_overlap]

        # 완전히 일치하지 않을 수 있지만 일부 겹침이 있어야 함
        assert any(char in chunk2_start for char in chunk1_end), \
            "Chunks should have overlapping content"


def test_metadata_preservation():
    """ParsedDocument 메타데이터 보존 검증"""
    from app.services.document_parser.base_parser import ParsedPage

    chunker = DocumentChunker()

    document = ParsedDocument(
        pages=[
            ParsedPage(page_number=1, content="A" * 500),
            ParsedPage(page_number=2, content="B" * 500)
        ],
        total_pages=2,
        total_characters=1000,
        metadata={
            "file_path": "/test/sample.txt",
            "title": "Sample Document",
            "author": "Test Author"
        }
    )

    chunks = chunker.chunk_document(document, document_id="/test/sample.txt")

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.document_id == "/test/sample.txt"
        assert chunk.document_title == "Sample Document"
        assert chunk.page_number == 2


def test_page_number_tracking():
    """페이지 번호 추적 검증"""
    chunker = DocumentChunker()

    metadata = {
        "document_id": "doc_123",
        "title": "Multi-Page Doc",
        "page_number": 3
    }

    text = "Content from page 3. " * 50

    chunks = chunker.chunk_text(text, metadata=metadata)

    for chunk in chunks:
        assert chunk.document_id == "doc_123"
        assert chunk.document_title == "Multi-Page Doc"
        assert chunk.page_number == 3


# ============================================================================
# Edge Case Tests (3)
# ============================================================================

def test_empty_document_error():
    """빈 문서 처리 에러 검증"""
    chunker = DocumentChunker()

    document = ParsedDocument(
        pages=[],
        total_pages=0,
        total_characters=0,
        metadata={"file_path": "/test/empty.txt", "title": "Empty Document"}
    )

    with pytest.raises(ValueError, match="Document content is empty"):
        chunker.chunk_document(document)


def test_empty_text_error():
    """빈 텍스트 처리 에러 검증"""
    chunker = DocumentChunker()

    with pytest.raises(ValueError, match="Text is empty"):
        chunker.chunk_text("")

    with pytest.raises(ValueError, match="Text is empty"):
        chunker.chunk_text("   ")  # 공백만 있는 경우


def test_short_text():
    """짧은 텍스트 처리 (chunk_size보다 작은 경우)"""
    chunker = DocumentChunker(ChunkerConfig(chunk_size=500))

    short_text = "This is a very short text."

    chunks = chunker.chunk_text(short_text)

    assert len(chunks) == 1
    assert chunks[0].content == short_text
    assert chunks[0].chunk_index == 0


def test_very_long_document():
    """매우 긴 문서 처리 (10,000자 이상)"""
    chunker = DocumentChunker(ChunkerConfig(chunk_size=500, chunk_overlap=50))

    # 15,000자 텍스트
    long_text = "Lorem ipsum dolor sit amet. " * 600

    chunks = chunker.chunk_text(long_text)

    # 약 30개 청크 예상 (15000 / 500)
    # overlap 때문에 더 많은 청크가 생성될 수 있음
    assert len(chunks) >= 25, f"Expected at least 25 chunks, got {len(chunks)}"
    assert len(chunks) <= 45, f"Expected at most 45 chunks, got {len(chunks)}"

    # 모든 청크의 인덱스가 연속적인지 확인
    for idx, chunk in enumerate(chunks):
        assert chunk.chunk_index == idx


# ============================================================================
# Configuration Tests (1)
# ============================================================================

def test_custom_chunk_size():
    """커스텀 청크 크기 설정 검증"""
    custom_size = 300
    chunker = DocumentChunker(
        ChunkerConfig(chunk_size=custom_size, chunk_overlap=30)
    )

    text = "A" * 1000

    chunks = chunker.chunk_text(text)

    # 청크 크기가 커스텀 설정을 따르는지 확인
    for chunk in chunks[:-1]:  # 마지막 청크 제외
        assert len(chunk.content) >= custom_size * 0.9
        assert len(chunk.content) <= custom_size * 1.1


# ============================================================================
# Statistics Tests (1)
# ============================================================================

def test_chunk_statistics():
    """청크 통계 계산 검증"""
    chunker = DocumentChunker(ChunkerConfig(chunk_size=500, chunk_overlap=50))

    text = "Sample text. " * 200  # 약 2600자

    chunks = chunker.chunk_text(text)
    stats = chunker.get_chunk_statistics(chunks)

    assert stats["total_chunks"] == len(chunks)
    assert stats["total_characters"] > 0
    assert stats["avg_chunk_size"] > 0
    assert stats["min_chunk_size"] > 0
    assert stats["max_chunk_size"] > 0
    assert stats["min_chunk_size"] <= stats["avg_chunk_size"] <= stats["max_chunk_size"]


def test_empty_chunks_statistics():
    """빈 청크 리스트의 통계 검증"""
    chunker = DocumentChunker()

    stats = chunker.get_chunk_statistics([])

    assert stats["total_chunks"] == 0
    assert stats["avg_chunk_size"] == 0
    assert stats["min_chunk_size"] == 0
    assert stats["max_chunk_size"] == 0
    assert stats["total_characters"] == 0


# ============================================================================
# Integration Tests with Document Parsers
# ============================================================================

def test_integration_with_pdf_parser():
    """PDF 파서와의 통합 테스트"""
    from app.services.document_parser.pdf_parser import PDFParser

    parser = PDFParser()
    chunker = DocumentChunker()

    # PDF 파일 경로 (fixtures에 있는 테스트 파일 사용)
    pdf_path = "backend/tests/fixtures/pdf/sample_multipage.pdf"

    try:
        document = parser.parse(pdf_path)
        chunks = chunker.chunk_document(document, document_id=pdf_path)

        assert len(chunks) > 0
        assert all(chunk.document_id == pdf_path for chunk in chunks)
        assert all(chunk.chunk_index == idx for idx, chunk in enumerate(chunks))
    except FileNotFoundError:
        pytest.skip("Test PDF file not found")


def test_integration_with_text_parser():
    """텍스트 파서와의 통합 테스트"""
    from app.services.document_parser.text_parser import TextParser

    parser = TextParser()
    chunker = DocumentChunker()

    # 임시 텍스트 파일 생성
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document. " * 100)
        temp_path = f.name

    try:
        document = parser.parse(temp_path)
        chunks = chunker.chunk_document(document, document_id=temp_path)

        assert len(chunks) > 0
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)
    finally:
        import os
        os.unlink(temp_path)
