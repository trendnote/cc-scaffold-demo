"""
PDF 파서 테스트 (TDD)

10개 테스트 케이스:
- Happy Path: TC01, TC02, TC03 (정상 시나리오)
- Edge Cases: TC04, TC05, TC06 (경계 조건)
- Error Handling: TC07, TC08, TC09 (에러 처리)
- Security: TC10 (보안)
"""

import pytest
from pathlib import Path
from app.services.document_parser.pdf_parser import PDFParser
from app.services.document_parser.base_parser import (
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
    EncryptedFileError,
    MaliciousFileError,
)

# Fixtures 디렉토리 경로
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "pdf"


@pytest.fixture
def pdf_parser():
    """기본 PDF 파서 fixture"""
    return PDFParser()


@pytest.fixture
def pdf_parser_custom_config():
    """커스텀 설정 PDF 파서 fixture"""
    config = ParserConfig(max_file_size_mb=50, skip_empty_pages=True)
    return PDFParser(config=config)


# ============================================
# Happy Path Tests (정상 시나리오)
# ============================================

def test_valid_pdf_parsing(pdf_parser):
    """
    TC01: 정상 PDF 파싱
    - 입력: 2페이지 샘플 PDF (sample_valid.pdf)
    - 기대 결과:
      - total_pages == 2
      - 각 페이지 content 존재
      - page_number 정확
    """
    pdf_path = FIXTURES_DIR / "sample_valid.pdf"
    result = pdf_parser.parse(str(pdf_path))

    assert result.total_pages == 2
    assert len(result.pages) == 2
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert len(result.pages[0].content) > 0
    assert len(result.pages[1].content) > 0
    assert result.total_characters > 0


def test_page_number_extraction(pdf_parser):
    """
    TC02: 페이지 번호 추출 정확성
    - 입력: 5페이지 PDF (sample_5pages.pdf)
    - 기대 결과: page_number가 1, 2, 3, 4, 5 순서대로
    """
    pdf_path = FIXTURES_DIR / "sample_5pages.pdf"
    result = pdf_parser.parse(str(pdf_path))

    assert result.total_pages == 5
    for i, page in enumerate(result.pages, start=1):
        assert page.page_number == i


def test_multi_page_pdf(pdf_parser):
    """
    TC03: 다중 페이지 PDF 파싱
    - 입력: 10페이지 PDF (sample_10pages.pdf)
    - 기대 결과:
      - total_pages == 10
      - 모든 페이지 content 존재
    """
    pdf_path = FIXTURES_DIR / "sample_10pages.pdf"
    result = pdf_parser.parse(str(pdf_path))

    assert result.total_pages == 10
    assert len(result.pages) == 10
    for page in result.pages:
        assert len(page.content) > 0


# ============================================
# Edge Cases (경계 조건)
# ============================================

def test_empty_page_skip(pdf_parser):
    """
    TC04: 빈 페이지 건너뛰기
    - 입력: 3페이지 PDF (2번째 페이지 빈 페이지, sample_with_empty_page.pdf)
    - 기대 결과:
      - total_pages == 3 (원본 페이지 수)
      - pages 리스트에는 빈 페이지 제외 (2개)
    """
    pdf_path = FIXTURES_DIR / "sample_with_empty_page.pdf"
    result = pdf_parser.parse(str(pdf_path))

    assert result.total_pages == 3
    # skip_empty_pages=True일 때 빈 페이지 제외
    assert len(result.pages) == 2
    assert all(len(page.content.strip()) > 0 for page in result.pages)


def test_large_pdf_handling(pdf_parser_custom_config):
    """
    TC05: 대용량 PDF 처리 (한계 테스트)
    - 입력: 49MB PDF (sample_large_49mb.pdf) - 제한 50MB
    - 기대 결과: 정상 파싱 성공
    """
    pdf_path = FIXTURES_DIR / "sample_large_49mb.pdf"

    # 파일이 없으면 스킵 (수동 생성 필요)
    if not pdf_path.exists():
        pytest.skip("Large PDF test file not found (manual creation required)")

    result = pdf_parser_custom_config.parse(str(pdf_path))

    assert result.total_pages > 0
    assert result.total_characters > 0


def test_pdf_with_images_only(pdf_parser):
    """
    TC06: 이미지만 있는 PDF
    - 입력: 이미지만 포함된 PDF (sample_images_only.pdf)
    - 기대 결과:
      - total_pages > 0
      - content는 빈 문자열 (텍스트 없음)
      - 에러 발생하지 않음
    """
    pdf_path = FIXTURES_DIR / "sample_images_only.pdf"
    result = pdf_parser.parse(str(pdf_path))

    assert result.total_pages > 0
    # 이미지만 있는 경우 텍스트 추출 불가
    for page in result.pages:
        assert page.content == "" or page.content.strip() == ""


# ============================================
# Error Handling (에러 처리)
# ============================================

def test_corrupted_pdf_error(pdf_parser):
    """
    TC07: 손상된 PDF 에러 처리
    - 입력: 손상된 PDF 파일 (sample_corrupted.pdf)
    - 기대 결과: CorruptedFileError 발생
    """
    pdf_path = FIXTURES_DIR / "sample_corrupted.pdf"

    with pytest.raises(CorruptedFileError) as exc_info:
        pdf_parser.parse(str(pdf_path))

    assert "손상된" in str(exc_info.value) or "corrupted" in str(exc_info.value).lower()


def test_encrypted_pdf_warning(pdf_parser):
    """
    TC08: 암호화된 PDF 경고
    - 입력: 암호화된 PDF (sample_encrypted.pdf)
    - 기대 결과: EncryptedFileError 발생
    """
    pdf_path = FIXTURES_DIR / "sample_encrypted.pdf"

    with pytest.raises(EncryptedFileError) as exc_info:
        pdf_parser.parse(str(pdf_path))

    assert "암호화" in str(exc_info.value) or "encrypted" in str(exc_info.value).lower()


def test_file_size_limit_exceeded(pdf_parser):
    """
    TC09: 파일 크기 제한 초과 [HARD RULE]
    - 입력: 150MB PDF (sample_large_150mb.pdf) - 제한 100MB
    - 기대 결과: FileSizeLimitExceededError 발생
    """
    pdf_path = FIXTURES_DIR / "sample_large_150mb.pdf"

    # 파일이 없으면 스킵 (수동 생성 필요)
    if not pdf_path.exists():
        pytest.skip("Large PDF test file not found (manual creation required)")

    with pytest.raises(FileSizeLimitExceededError) as exc_info:
        pdf_parser.parse(str(pdf_path))

    assert "100" in str(exc_info.value)  # 제한 크기 명시
    assert "150" in str(exc_info.value)  # 실제 크기 명시


# ============================================
# Security Tests (보안)
# ============================================

def test_malicious_pdf_rejection(pdf_parser):
    """
    TC10: 악성 PDF 거부 [HARD RULE]
    - 입력: JavaScript 포함 PDF (sample_malicious_js.pdf)
    - 기대 결과: MaliciousFileError 발생 또는 안전하게 처리
    """
    pdf_path = FIXTURES_DIR / "sample_malicious_js.pdf"

    # 악성 PDF는 파싱 거부하거나, JavaScript 실행하지 않고 텍스트만 추출
    try:
        result = pdf_parser.parse(str(pdf_path))
        # 안전하게 처리된 경우: JavaScript 코드가 content에 없어야 함
        for page in result.pages:
            assert "eval(" not in page.content.lower()
            assert "javascript:" not in page.content.lower()
    except MaliciousFileError:
        # 악성 PDF 거부 (더 안전한 방법)
        pass
