"""
문서 파서 팩토리 테스트

테스트 케이스:
- Factory: TC01~TC05 (팩토리 기능)
- Integration: TC06~TC09 (통합 테스트)
"""

import pytest
from pathlib import Path
from app.services.document_parser.factory import DocumentParserFactory
from app.services.document_parser.base_parser import (
    ParserConfig,
    UnsupportedFileTypeError,
)
from app.services.document_parser.pdf_parser import PDFParser
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.text_parser import TextParser
from app.services.document_parser.markdown_parser import MarkdownParser

# Fixtures 디렉토리 경로
PDF_FIXTURES = Path(__file__).parent / "fixtures" / "pdf"
DOCX_FIXTURES = Path(__file__).parent / "fixtures" / "docx"
TXT_FIXTURES = Path(__file__).parent / "fixtures" / "txt"
MD_FIXTURES = Path(__file__).parent / "fixtures" / "markdown"


# ============================================
# Factory Tests (팩토리 기능)
# ============================================

def test_get_pdf_parser():
    """
    TC01: PDF 파서 선택
    - 입력: .pdf 파일 경로
    - 기대 결과: PDFParser 인스턴스 반환
    """
    pdf_path = PDF_FIXTURES / "sample_valid.pdf"
    parser = DocumentParserFactory.get_parser(str(pdf_path))

    assert isinstance(parser, PDFParser)


def test_get_docx_parser():
    """
    TC02: DOCX 파서 선택
    - 입력: .docx 파일 경로
    - 기대 결과: DOCXParser 인스턴스 반환
    """
    docx_path = DOCX_FIXTURES / "sample_valid.docx"
    parser = DocumentParserFactory.get_parser(str(docx_path))

    assert isinstance(parser, DOCXParser)


def test_get_text_parser():
    """
    TC03: TXT 파서 선택
    - 입력: .txt 파일 경로
    - 기대 결과: TextParser 인스턴스 반환
    """
    txt_path = TXT_FIXTURES / "sample_valid.txt"
    parser = DocumentParserFactory.get_parser(str(txt_path))

    assert isinstance(parser, TextParser)


def test_get_markdown_parser():
    """
    TC04: Markdown 파서 선택
    - 입력: .md 파일 경로
    - 기대 결과: MarkdownParser 인스턴스 반환
    """
    md_path = MD_FIXTURES / "sample_valid.md"
    parser = DocumentParserFactory.get_parser(str(md_path))

    assert isinstance(parser, MarkdownParser)


def test_unsupported_file_type():
    """
    TC05: 지원하지 않는 파일 타입
    - 입력: .xyz 파일
    - 기대 결과: UnsupportedFileTypeError 발생
    """
    # 임시 파일 생성
    temp_file = Path("temp.xyz")
    temp_file.write_text("test")

    try:
        with pytest.raises(UnsupportedFileTypeError) as exc_info:
            DocumentParserFactory.get_parser(str(temp_file))

        assert ".xyz" in str(exc_info.value)
        assert "지원하지 않는" in str(exc_info.value) or "unsupported" in str(exc_info.value).lower()
    finally:
        # 정리
        if temp_file.exists():
            temp_file.unlink()


# ============================================
# Integration Tests (통합 테스트)
# ============================================

def test_parse_pdf_via_factory():
    """
    TC06: 팩토리를 통한 PDF 파싱
    - 입력: PDF 파일
    - 기대 결과: 정상 파싱
    """
    pdf_path = PDF_FIXTURES / "sample_valid.pdf"
    parser = DocumentParserFactory.get_parser(str(pdf_path))
    result = parser.parse(str(pdf_path))

    assert result.total_pages > 0
    assert result.total_characters > 0


def test_parse_docx_via_factory():
    """
    TC07: 팩토리를 통한 DOCX 파싱
    - 입력: DOCX 파일
    - 기대 결과: 정상 파싱
    """
    docx_path = DOCX_FIXTURES / "sample_valid.docx"
    parser = DocumentParserFactory.get_parser(str(docx_path))
    result = parser.parse(str(docx_path))

    assert result.total_pages == 1
    assert result.total_characters > 0
    assert "Sample DOCX Document" in result.pages[0].content


def test_parse_txt_via_factory():
    """
    TC08: 팩토리를 통한 TXT 파싱
    - 입력: TXT 파일
    - 기대 결과: 정상 파싱
    """
    txt_path = TXT_FIXTURES / "sample_valid.txt"
    parser = DocumentParserFactory.get_parser(str(txt_path))
    result = parser.parse(str(txt_path))

    assert result.total_pages == 1
    assert result.total_characters > 0
    assert "Sample TXT Document" in result.pages[0].content


def test_parse_markdown_via_factory():
    """
    TC09: 팩토리를 통한 Markdown 파싱
    - 입력: Markdown 파일
    - 기대 결과: 정상 파싱
    """
    md_path = MD_FIXTURES / "sample_valid.md"
    parser = DocumentParserFactory.get_parser(str(md_path))
    result = parser.parse(str(md_path))

    assert result.total_pages == 1
    assert result.total_characters > 0
    assert "Sample Markdown Document" in result.pages[0].content


# ============================================
# Utility Methods Tests
# ============================================

def test_get_supported_extensions():
    """
    TC10: 지원하는 확장자 목록 조회
    - 기대 결과: [".pdf", ".docx", ".txt", ".md", ".markdown"]
    """
    extensions = DocumentParserFactory.get_supported_extensions()

    assert ".pdf" in extensions
    assert ".docx" in extensions
    assert ".txt" in extensions
    assert ".md" in extensions
    assert ".markdown" in extensions


def test_is_supported():
    """
    TC11: 파일 지원 여부 확인
    - 기대 결과:
      - .pdf: True
      - .docx: True
      - .xyz: False
    """
    assert DocumentParserFactory.is_supported("test.pdf") is True
    assert DocumentParserFactory.is_supported("test.docx") is True
    assert DocumentParserFactory.is_supported("test.txt") is True
    assert DocumentParserFactory.is_supported("test.md") is True
    assert DocumentParserFactory.is_supported("test.xyz") is False


def test_custom_config_via_factory():
    """
    TC12: 팩토리를 통한 커스텀 설정 적용
    - 입력: 커스텀 ParserConfig
    - 기대 결과: 설정이 파서에 적용됨
    """
    config = ParserConfig(max_file_size_mb=50, skip_empty_pages=False)
    txt_path = TXT_FIXTURES / "sample_valid.txt"
    parser = DocumentParserFactory.get_parser(str(txt_path), config=config)

    assert parser.config.max_file_size_mb == 50
    assert parser.config.skip_empty_pages is False


def test_case_insensitive_extension():
    """
    TC13: 대소문자 구분 없는 확장자 처리
    - 입력: .PDF, .Docx, .TXT, .MD
    - 기대 결과: 정상 파서 반환
    """
    # 임시 파일 생성
    temp_pdf = Path("temp.PDF")
    temp_docx = Path("temp.Docx")
    temp_txt = Path("temp.TXT")
    temp_md = Path("temp.MD")

    temp_pdf.write_bytes(b"dummy")
    temp_docx.write_bytes(b"dummy")
    temp_txt.write_text("dummy")
    temp_md.write_text("dummy")

    try:
        assert isinstance(DocumentParserFactory.get_parser(str(temp_pdf)), PDFParser)
        assert isinstance(DocumentParserFactory.get_parser(str(temp_docx)), DOCXParser)
        assert isinstance(DocumentParserFactory.get_parser(str(temp_txt)), TextParser)
        assert isinstance(DocumentParserFactory.get_parser(str(temp_md)), MarkdownParser)
    finally:
        # 정리
        temp_pdf.unlink(missing_ok=True)
        temp_docx.unlink(missing_ok=True)
        temp_txt.unlink(missing_ok=True)
        temp_md.unlink(missing_ok=True)
