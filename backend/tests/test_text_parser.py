"""
TXT 파서 테스트

테스트 케이스:
- Happy Path: TC01, TC02, TC03 (정상 시나리오)
- Edge Cases: TC04 (경계 조건)
"""

import pytest
from pathlib import Path
from app.services.document_parser.text_parser import TextParser
from app.services.document_parser.base_parser import (
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
)

# Fixtures 디렉토리 경로
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "txt"


@pytest.fixture
def text_parser():
    """기본 TXT 파서 fixture"""
    return TextParser()


@pytest.fixture
def text_parser_custom_config():
    """커스텀 설정 TXT 파서 fixture"""
    config = ParserConfig(max_file_size_mb=50, skip_empty_pages=True)
    return TextParser(config=config)


# ============================================
# Happy Path Tests (정상 시나리오)
# ============================================

def test_valid_txt_parsing(text_parser):
    """
    TC01: 정상 TXT 파싱
    - 입력: 정상 TXT 파일 (sample_valid.txt)
    - 기대 결과:
      - total_pages == 1
      - content 존재
      - total_characters > 0
    """
    txt_path = FIXTURES_DIR / "sample_valid.txt"
    result = text_parser.parse(str(txt_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert len(result.pages[0].content) > 0
    assert result.total_characters > 0
    assert "Sample TXT Document" in result.pages[0].content


def test_unicode_txt_parsing(text_parser):
    """
    TC02: 다국어 TXT 파싱
    - 입력: 다국어 TXT 파일 (sample_unicode.txt)
    - 기대 결과:
      - 다양한 언어 정상 추출
      - 인코딩 문제 없음
    """
    txt_path = FIXTURES_DIR / "sample_unicode.txt"
    result = text_parser.parse(str(txt_path))

    assert result.total_pages == 1
    assert len(result.pages[0].content) > 0
    assert "안녕하세요" in result.pages[0].content
    assert "こんにちは" in result.pages[0].content
    assert "你好" in result.pages[0].content


def test_large_txt_parsing(text_parser_custom_config):
    """
    TC03: 대용량 TXT 파싱
    - 입력: 많은 라인을 포함한 TXT (sample_large.txt)
    - 기대 결과:
      - 정상 파싱
      - 모든 내용 추출
    """
    txt_path = FIXTURES_DIR / "sample_large.txt"
    result = text_parser_custom_config.parse(str(txt_path))

    assert result.total_pages == 1
    assert result.total_characters > 1000  # 충분히 큰 파일
    assert "Large TXT Document" in result.pages[0].content


# ============================================
# Edge Cases (경계 조건)
# ============================================

def test_empty_txt_handling(text_parser):
    """
    TC04: 빈 TXT 파일
    - 입력: 빈 TXT (sample_empty.txt)
    - 기대 결과:
      - total_pages == 1
      - content는 빈 문자열
      - 에러 발생하지 않음
    """
    txt_path = FIXTURES_DIR / "sample_empty.txt"
    result = text_parser.parse(str(txt_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].content == ""


# ============================================
# Error Handling (에러 처리)
# ============================================

def test_file_not_found_error(text_parser):
    """
    TC05: 파일 없음 에러
    - 입력: 존재하지 않는 파일
    - 기대 결과: FileNotFoundError 발생
    """
    with pytest.raises(FileNotFoundError):
        text_parser.parse("nonexistent.txt")


def test_metadata_extraction(text_parser):
    """
    TC06: 메타데이터 추출
    - 입력: 정상 TXT 파일
    - 기대 결과:
      - line_count, word_count 포함
    """
    txt_path = FIXTURES_DIR / "sample_valid.txt"
    result = text_parser.parse(str(txt_path))

    assert "line_count" in result.metadata
    assert "word_count" in result.metadata
    assert result.metadata["line_count"] > 0
    assert result.metadata["word_count"] > 0
