"""
DOCX 파서 테스트

테스트 케이스:
- Happy Path: TC01, TC02, TC03 (정상 시나리오)
- Edge Cases: TC04 (경계 조건)
"""

import pytest
from pathlib import Path
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.base_parser import (
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
)

# Fixtures 디렉토리 경로
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "docx"


@pytest.fixture
def docx_parser():
    """기본 DOCX 파서 fixture"""
    return DOCXParser()


@pytest.fixture
def docx_parser_custom_config():
    """커스텀 설정 DOCX 파서 fixture"""
    config = ParserConfig(max_file_size_mb=50, skip_empty_pages=True)
    return DOCXParser(config=config)


# ============================================
# Happy Path Tests (정상 시나리오)
# ============================================

def test_valid_docx_parsing(docx_parser):
    """
    TC01: 정상 DOCX 파싱
    - 입력: 정상 DOCX 파일 (sample_valid.docx)
    - 기대 결과:
      - total_pages == 1 (DOCX는 단일 페이지로 처리)
      - content 존재
      - total_characters > 0
    """
    docx_path = FIXTURES_DIR / "sample_valid.docx"
    result = docx_parser.parse(str(docx_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert len(result.pages[0].content) > 0
    assert result.total_characters > 0
    assert "Sample DOCX Document" in result.pages[0].content


def test_korean_docx_parsing(docx_parser):
    """
    TC02: 한글 DOCX 파싱
    - 입력: 한글 DOCX 파일 (sample_korean.docx)
    - 기대 결과:
      - 한글 내용 정상 추출
      - 인코딩 문제 없음
    """
    docx_path = FIXTURES_DIR / "sample_korean.docx"
    result = docx_parser.parse(str(docx_path))

    assert result.total_pages == 1
    assert len(result.pages[0].content) > 0
    assert "한글 문서 테스트" in result.pages[0].content
    assert "가나다라마바사" in result.pages[0].content


def test_large_docx_parsing(docx_parser_custom_config):
    """
    TC03: 대용량 DOCX 파싱
    - 입력: 많은 단락을 포함한 DOCX (sample_large.docx)
    - 기대 결과:
      - 정상 파싱
      - 모든 내용 추출
    """
    docx_path = FIXTURES_DIR / "sample_large.docx"
    result = docx_parser_custom_config.parse(str(docx_path))

    assert result.total_pages == 1
    assert result.total_characters > 1000  # 충분히 큰 파일
    assert "Large DOCX Document" in result.pages[0].content


# ============================================
# Edge Cases (경계 조건)
# ============================================

def test_empty_docx_handling(docx_parser):
    """
    TC04: 빈 DOCX 파일
    - 입력: 빈 DOCX (sample_empty.docx)
    - 기대 결과:
      - total_pages == 1
      - content는 빈 문자열
      - 에러 발생하지 않음
    """
    docx_path = FIXTURES_DIR / "sample_empty.docx"
    result = docx_parser.parse(str(docx_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].content.strip() == ""


# ============================================
# Error Handling (에러 처리)
# ============================================

def test_file_not_found_error(docx_parser):
    """
    TC05: 파일 없음 에러
    - 입력: 존재하지 않는 파일
    - 기대 결과: FileNotFoundError 발생
    """
    with pytest.raises(FileNotFoundError):
        docx_parser.parse("nonexistent.docx")


def test_corrupted_docx_error(docx_parser):
    """
    TC06: 손상된 DOCX 에러
    - 입력: 손상된 DOCX 파일 (txt 파일을 .docx로 위장)
    - 기대 결과: CorruptedFileError 발생
    """
    # 손상된 DOCX 파일 생성 (임시)
    corrupted_path = FIXTURES_DIR / "corrupted.docx"
    with open(corrupted_path, "w") as f:
        f.write("This is not a valid DOCX file")

    try:
        with pytest.raises(CorruptedFileError):
            docx_parser.parse(str(corrupted_path))
    finally:
        # 테스트 후 정리
        if corrupted_path.exists():
            corrupted_path.unlink()
