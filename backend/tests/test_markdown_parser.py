"""
Markdown 파서 테스트

테스트 케이스:
- Happy Path: TC01, TC02, TC03 (정상 시나리오)
- Edge Cases: TC04 (경계 조건)
"""

import pytest
from pathlib import Path
from app.services.document_parser.markdown_parser import MarkdownParser
from app.services.document_parser.base_parser import (
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
)

# Fixtures 디렉토리 경로
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "markdown"


@pytest.fixture
def markdown_parser():
    """기본 Markdown 파서 fixture"""
    return MarkdownParser()


@pytest.fixture
def markdown_parser_custom_config():
    """커스텀 설정 Markdown 파서 fixture"""
    config = ParserConfig(max_file_size_mb=50, skip_empty_pages=True)
    return MarkdownParser(config=config)


# ============================================
# Happy Path Tests (정상 시나리오)
# ============================================

def test_valid_markdown_parsing(markdown_parser):
    """
    TC01: 정상 Markdown 파싱
    - 입력: 정상 Markdown 파일 (sample_valid.md)
    - 기대 결과:
      - total_pages == 1
      - content 존재
      - total_characters > 0
    """
    md_path = FIXTURES_DIR / "sample_valid.md"
    result = markdown_parser.parse(str(md_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert len(result.pages[0].content) > 0
    assert result.total_characters > 0
    assert "Sample Markdown Document" in result.pages[0].content


def test_korean_markdown_parsing(markdown_parser):
    """
    TC02: 한글 Markdown 파싱
    - 입력: 한글 Markdown 파일 (sample_korean.md)
    - 기대 결과:
      - 한글 내용 정상 추출
      - 인코딩 문제 없음
    """
    md_path = FIXTURES_DIR / "sample_korean.md"
    result = markdown_parser.parse(str(md_path))

    assert result.total_pages == 1
    assert len(result.pages[0].content) > 0
    assert "한글 마크다운 테스트" in result.pages[0].content
    assert "리스트 아이템" in result.pages[0].content


def test_readme_markdown_parsing(markdown_parser_custom_config):
    """
    TC03: README 스타일 Markdown 파싱
    - 입력: README 스타일 Markdown (sample_readme.md)
    - 기대 결과:
      - 정상 파싱
      - 다양한 Markdown 요소 포함
    """
    md_path = FIXTURES_DIR / "sample_readme.md"
    result = markdown_parser_custom_config.parse(str(md_path))

    assert result.total_pages == 1
    assert result.total_characters > 100
    assert "Project Title" in result.pages[0].content


# ============================================
# Edge Cases (경계 조건)
# ============================================

def test_empty_markdown_handling(markdown_parser):
    """
    TC04: 빈 Markdown 파일
    - 입력: 빈 Markdown (sample_empty.md)
    - 기대 결과:
      - total_pages == 1
      - content는 빈 문자열
      - 에러 발생하지 않음
    """
    md_path = FIXTURES_DIR / "sample_empty.md"
    result = markdown_parser.parse(str(md_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.pages[0].content == ""


# ============================================
# Metadata Tests (메타데이터 추출)
# ============================================

def test_markdown_metadata_extraction(markdown_parser):
    """
    TC05: Markdown 메타데이터 추출
    - 입력: 정상 Markdown 파일
    - 기대 결과:
      - heading_count, code_block_count, link_count, image_count 포함
    """
    md_path = FIXTURES_DIR / "sample_valid.md"
    result = markdown_parser.parse(str(md_path))

    assert "heading_count" in result.metadata
    assert "code_block_count" in result.metadata
    assert "link_count" in result.metadata
    assert "image_count" in result.metadata

    # sample_valid.md에는 헤딩, 코드 블록, 링크, 이미지가 포함되어 있음
    assert result.metadata["heading_count"] > 0
    assert result.metadata["code_block_count"] > 0
    assert result.metadata["link_count"] > 0
    assert result.metadata["image_count"] > 0


def test_file_metadata_extraction(markdown_parser):
    """
    TC06: 파일 메타데이터 추출
    - 입력: 정상 Markdown 파일
    - 기대 결과:
      - file_name, line_count, word_count 포함
    """
    md_path = FIXTURES_DIR / "sample_valid.md"
    result = markdown_parser.parse(str(md_path))

    assert "file_name" in result.metadata
    assert "line_count" in result.metadata
    assert "word_count" in result.metadata
    assert result.metadata["file_name"] == "sample_valid.md"
    assert result.metadata["line_count"] > 0
    assert result.metadata["word_count"] > 0


# ============================================
# Error Handling (에러 처리)
# ============================================

def test_file_not_found_error(markdown_parser):
    """
    TC07: 파일 없음 에러
    - 입력: 존재하지 않는 파일
    - 기대 결과: FileNotFoundError 발생
    """
    with pytest.raises(FileNotFoundError):
        markdown_parser.parse("nonexistent.md")
