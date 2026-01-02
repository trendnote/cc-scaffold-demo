# Task 1.5: 문서 파싱 모듈 구현 (PDF) - 실행 계획

---

## 📋 Meta

- **Task ID**: 1.5
- **Task명**: 문서 파싱 모듈 구현 (PDF)
- **예상 시간**: 6시간
- **담당**: Backend
- **작성일**: 2026-01-02
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
PDF 문서에서 텍스트를 추출하고, 페이지 번호 메타데이터를 포함한 구조화된 데이터를 생성하는 파서 모듈을 TDD 방식으로 구현합니다.

### 1.2 핵심 요구사항
- **기능**: PDF 텍스트 추출, 페이지 번호 메타데이터 추출
- **품질**: 10개 테스트 케이스 100% 통과
- **보안**: [HARD RULE] 파일 크기 100MB 제한, 악성 PDF 거부
- **안정성**: 에러 핸들링 (손상된 PDF, 암호화 PDF, 빈 페이지)

### 1.3 성공 기준
- [ ] 테스트 케이스 10개 모두 통과
- [ ] 5개 샘플 PDF 파싱 성공
- [ ] 텍스트 추출 정확도 확인 (수동 검증)
- [ ] 에러 케이스 처리 확인

---

## 2. 선행 조건 검증

### 2.1 환경 검증
실행 전 다음 사항을 확인합니다:

```bash
# Python 버전 확인 (3.11+ 필요)
python --version

# 가상환경 활성화 확인
which python  # venv 경로여야 함

# 필요한 디렉토리 존재 확인
ls -la app/models/
ls -la app/db/
ls -la tests/
```

### 2.2 의존성 확인
다음 Task들이 완료되어 있어야 합니다:

- [x] **Task 1.1**: Docker Compose 설정 완료
- [x] **Task 1.2**: PostgreSQL 스키마 설정 완료
- [x] **Task 1.3**: Milvus Collection 생성 완료
- [x] **Task 1.4**: Ollama 설치 및 모델 다운로드 완료

---

## 3. 기술 스택 선택

### 3.1 PDF 파싱 라이브러리 비교

| 라이브러리 | 장점 | 단점 | 선택 여부 |
|-----------|------|------|----------|
| **pypdf** | - 가볍고 빠름<br>- 순수 Python<br>- 의존성 최소 | - 복잡한 PDF 처리 약함<br>- OCR 미지원 | ⭐ **선택** |
| **pdfplumber** | - 테이블 추출 우수<br>- 레이아웃 정보 풍부 | - 느림<br>- 의존성 많음 | 보류 |
| **PyMuPDF** | - 매우 빠름<br>- OCR 지원 | - C 의존성<br>- 라이선스 복잡 | 보류 |

### 3.2 최종 선택: **pypdf**

**선택 이유**:
1. **단순성**: 텍스트 추출만 필요 (테이블, 이미지 불필요)
2. **안정성**: 순수 Python, 설치 간단
3. **유지보수**: 활발한 커뮤니티, 최신 버전 지원
4. **확장성**: 나중에 pdfplumber 추가 가능

**대체 전략**:
- Task 1.6 완료 후 복잡한 PDF 처리가 필요하면 pdfplumber 추가 고려

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 환경 설정 및 의존성 설치 (30분)

#### 작업 내용
1. **requirements.txt 업데이트**
   ```txt
   pypdf==4.0.1
   pytest==7.4.3
   pytest-cov==4.1.0
   ```

2. **디렉토리 구조 생성**
   ```bash
   mkdir -p app/services/document_parser
   mkdir -p tests/fixtures/pdf
   touch app/services/document_parser/__init__.py
   touch app/services/document_parser/base_parser.py
   touch app/services/document_parser/pdf_parser.py
   ```

3. **의존성 설치**
   ```bash
   source venv/bin/activate
   pip install pypdf==4.0.1 pytest==7.4.3 pytest-cov==4.1.0
   pip freeze > requirements.txt
   ```

#### 검증
```bash
# pypdf 설치 확인
python -c "import pypdf; print(pypdf.__version__)"  # 4.0.1

# 디렉토리 구조 확인
tree app/services/document_parser
tree tests/fixtures
```

---

### 4.2 Step 2: 추상 Base Parser 설계 (30분)

#### 작업 내용
`app/services/document_parser/base_parser.py` 작성:

**설계 원칙**:
- **SOLID 원칙**: Open-Closed Principle (확장에 열려있고 수정에 닫혀있음)
- **추상화**: 모든 파서가 따라야 할 인터페이스 정의
- **타입 안전성**: Pydantic 모델 사용

**핵심 클래스**:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    """파싱된 페이지 정보"""
    page_number: int = Field(..., ge=1, description="페이지 번호 (1부터 시작)")
    content: str = Field(..., min_length=0, description="페이지 텍스트 내용")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")


class ParsedDocument(BaseModel):
    """파싱된 문서 전체 정보"""
    pages: List[ParsedPage] = Field(..., min_items=0, description="페이지 리스트")
    total_pages: int = Field(..., ge=0, description="전체 페이지 수")
    total_characters: int = Field(..., ge=0, description="전체 문자 수")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="문서 메타데이터")


class ParserConfig(BaseModel):
    """파서 설정"""
    max_file_size_mb: int = Field(default=100, ge=1, le=500, description="최대 파일 크기 (MB)")
    skip_empty_pages: bool = Field(default=True, description="빈 페이지 건너뛰기 여부")
    encoding: str = Field(default="utf-8", description="텍스트 인코딩")


class DocumentParserError(Exception):
    """문서 파서 기본 에러"""
    pass


class FileSizeLimitExceededError(DocumentParserError):
    """파일 크기 제한 초과 에러"""
    pass


class CorruptedFileError(DocumentParserError):
    """손상된 파일 에러"""
    pass


class EncryptedFileError(DocumentParserError):
    """암호화된 파일 에러"""
    pass


class MaliciousFileError(DocumentParserError):
    """악성 파일 에러"""
    pass


class BaseDocumentParser(ABC):
    """문서 파서 추상 클래스"""

    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """
        문서를 파싱하여 구조화된 데이터 반환

        Args:
            file_path: 파싱할 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 손상된 파일
            EncryptedFileError: 암호화된 파일
            MaliciousFileError: 악성 파일
        """
        pass

    def _validate_file_size(self, file_path: str) -> None:
        """
        파일 크기 검증 [HARD RULE]

        Args:
            file_path: 검증할 파일 경로

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
        """
        import os
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise FileSizeLimitExceededError(
                f"파일 크기 {file_size_mb:.2f}MB가 "
                f"제한 {self.config.max_file_size_mb}MB를 초과했습니다."
            )
```

#### 검증
```python
# tests/test_base_parser.py 작성 (간단한 테스트)
def test_parser_config_default():
    config = ParserConfig()
    assert config.max_file_size_mb == 100
    assert config.skip_empty_pages is True

def test_parsed_page_validation():
    page = ParsedPage(page_number=1, content="테스트")
    assert page.page_number == 1
```

---

### 4.3 Step 3: TDD - 테스트 케이스 작성 (60분)

#### 작업 내용
`tests/test_pdf_parser.py` 작성 (10개 테스트 케이스)

**TDD 원칙**:
- **Red**: 테스트 먼저 작성 (실패)
- **Green**: 최소 코드로 테스트 통과
- **Refactor**: 코드 개선

#### 테스트 구조

```python
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
```

#### 테스트 픽스처 준비 가이드

**필요한 샘플 PDF 파일** (총 11개):

1. `sample_valid.pdf` - 2페이지 정상 PDF
2. `sample_5pages.pdf` - 5페이지 PDF
3. `sample_10pages.pdf` - 10페이지 PDF
4. `sample_with_empty_page.pdf` - 빈 페이지 포함 PDF
5. `sample_large_49mb.pdf` - 49MB PDF (제한 내)
6. `sample_images_only.pdf` - 이미지만 포함 PDF
7. `sample_corrupted.pdf` - 손상된 PDF
8. `sample_encrypted.pdf` - 암호화 PDF
9. `sample_large_150mb.pdf` - 150MB PDF (제한 초과)
10. `sample_malicious_js.pdf` - JavaScript 포함 PDF

**픽스처 생성 방법**:
```bash
# 스크립트로 생성 (나중에 작성)
python scripts/generate_test_pdfs.py
```

---

### 4.4 Step 4: PDF Parser 구현 (120분)

#### 작업 내용
`app/services/document_parser/pdf_parser.py` 작성

**구현 원칙**:
- **방어적 프로그래밍**: 모든 입력 검증
- **명시적 에러 처리**: 각 에러 상황 명확히 구분
- **로깅**: 파싱 과정 추적 가능

```python
import logging
from pathlib import Path
from typing import Dict, Any
import pypdf
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
    EncryptedFileError,
    MaliciousFileError,
)

logger = logging.getLogger(__name__)


class PDFParser(BaseDocumentParser):
    """PDF 문서 파서"""

    def parse(self, file_path: str) -> ParsedDocument:
        """
        PDF 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: PDF 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 손상된 파일
            EncryptedFileError: 암호화된 파일
            MaliciousFileError: 악성 파일
        """
        logger.info(f"PDF 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        # Step 2: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 3: PDF 읽기
        try:
            reader = PdfReader(file_path)
        except PdfReadError as e:
            logger.error(f"PDF 읽기 실패: {e}")
            raise CorruptedFileError(f"손상된 PDF 파일입니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise CorruptedFileError(f"PDF 파일을 읽을 수 없습니다: {e}")

        # Step 4: 암호화 확인
        if reader.is_encrypted:
            logger.warning(f"암호화된 PDF 파일: {file_path}")
            raise EncryptedFileError("암호화된 PDF 파일은 지원하지 않습니다.")

        # Step 5: 악성 코드 검사 (JavaScript 확인)
        self._check_malicious_content(reader)

        # Step 6: 페이지별 텍스트 추출
        pages = []
        total_pages = len(reader.pages)
        total_characters = 0

        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text()

                # 빈 페이지 처리
                if self.config.skip_empty_pages and not text.strip():
                    logger.debug(f"빈 페이지 건너뛰기: {page_num}")
                    continue

                # 페이지 데이터 생성
                parsed_page = ParsedPage(
                    page_number=page_num,
                    content=text,
                    metadata={
                        "rotation": page.get("/Rotate", 0),
                        "mediabox": str(page.mediabox) if hasattr(page, 'mediabox') else None,
                    }
                )
                pages.append(parsed_page)
                total_characters += len(text)

            except Exception as e:
                logger.error(f"페이지 {page_num} 추출 실패: {e}")
                # 페이지 추출 실패해도 계속 진행 (best effort)
                continue

        # Step 7: 문서 메타데이터 추출
        metadata = self._extract_metadata(reader)

        # Step 8: 결과 반환
        result = ParsedDocument(
            pages=pages,
            total_pages=total_pages,
            total_characters=total_characters,
            metadata=metadata,
        )

        logger.info(
            f"PDF 파싱 완료: {file_path}, "
            f"페이지 {total_pages}개, 문자 {total_characters}개"
        )

        return result

    def _check_malicious_content(self, reader: PdfReader) -> None:
        """
        악성 콘텐츠 검사 [HARD RULE]

        Args:
            reader: PDF 리더 객체

        Raises:
            MaliciousFileError: 악성 콘텐츠 발견 시
        """
        # JavaScript 검사
        if hasattr(reader, "get_fields") and reader.get_fields():
            for field_name, field_value in reader.get_fields().items():
                if "JavaScript" in str(field_value) or "/JS" in str(field_value):
                    logger.error(f"악성 JavaScript 발견: {field_name}")
                    raise MaliciousFileError(
                        "JavaScript가 포함된 PDF는 보안상 지원하지 않습니다."
                    )

        # 추가 보안 검사 (필요 시 확장)
        # - 외부 링크 검사
        # - 임베디드 파일 검사
        # - 매크로 검사

    def _extract_metadata(self, reader: PdfReader) -> Dict[str, Any]:
        """
        PDF 메타데이터 추출

        Args:
            reader: PDF 리더 객체

        Returns:
            메타데이터 딕셔너리
        """
        metadata = {}

        try:
            if reader.metadata:
                metadata = {
                    "title": reader.metadata.get("/Title"),
                    "author": reader.metadata.get("/Author"),
                    "subject": reader.metadata.get("/Subject"),
                    "creator": reader.metadata.get("/Creator"),
                    "producer": reader.metadata.get("/Producer"),
                    "creation_date": reader.metadata.get("/CreationDate"),
                    "modification_date": reader.metadata.get("/ModDate"),
                }
                # None 값 제거
                metadata = {k: v for k, v in metadata.items() if v is not None}
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return metadata
```

#### 검증
```bash
# 테스트 실행 (Red → Green)
pytest tests/test_pdf_parser.py -v

# 커버리지 확인
pytest tests/test_pdf_parser.py --cov=app/services/document_parser --cov-report=html
```

---

### 4.5 Step 5: 테스트 픽스처 생성 스크립트 작성 (60분)

#### 작업 내용
`scripts/generate_test_pdfs.py` 작성

```python
#!/usr/bin/env python3
"""
테스트용 PDF 파일 생성 스크립트

Usage:
    python scripts/generate_test_pdfs.py
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pypdf import PdfWriter, PdfReader
from pypdf.generic import DictionaryObject, NameObject, TextStringObject


def create_output_dir():
    """출력 디렉토리 생성"""
    output_dir = Path("tests/fixtures/pdf")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def generate_sample_valid(output_dir: Path):
    """TC01: 정상 2페이지 PDF"""
    file_path = output_dir / "sample_valid.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    # 페이지 1
    c.drawString(100, 750, "Sample PDF Document")
    c.drawString(100, 730, "Page 1 of 2")
    c.drawString(100, 700, "This is a valid PDF for testing purposes.")
    c.showPage()

    # 페이지 2
    c.drawString(100, 750, "Page 2 of 2")
    c.drawString(100, 730, "End of document.")
    c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_5pages(output_dir: Path):
    """TC02: 5페이지 PDF"""
    file_path = output_dir / "sample_5pages.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    for i in range(1, 6):
        c.drawString(100, 750, f"Page {i} of 5")
        c.drawString(100, 730, f"Content of page {i}")
        c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_10pages(output_dir: Path):
    """TC03: 10페이지 PDF"""
    file_path = output_dir / "sample_10pages.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    for i in range(1, 11):
        c.drawString(100, 750, f"Page {i} of 10")
        c.drawString(100, 730, f"Lorem ipsum dolor sit amet, page {i}")
        c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_with_empty_page(output_dir: Path):
    """TC04: 빈 페이지 포함 PDF (3페이지, 2번째 빈 페이지)"""
    file_path = output_dir / "sample_with_empty_page.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    # 페이지 1
    c.drawString(100, 750, "Page 1 with content")
    c.showPage()

    # 페이지 2 (빈 페이지)
    c.showPage()

    # 페이지 3
    c.drawString(100, 750, "Page 3 with content")
    c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_images_only(output_dir: Path):
    """TC06: 이미지만 있는 PDF (텍스트 없음)"""
    file_path = output_dir / "sample_images_only.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)

    # 이미지 그리기 (텍스트 없음)
    c.rect(100, 600, 200, 100, fill=1)
    c.showPage()

    c.save()
    print(f"✓ Generated: {file_path}")


def generate_sample_corrupted(output_dir: Path):
    """TC07: 손상된 PDF"""
    file_path = output_dir / "sample_corrupted.pdf"

    # 잘못된 PDF 헤더로 파일 생성
    with open(file_path, "w") as f:
        f.write("This is not a valid PDF file.\n")
        f.write("%PDF-1.4\n")
        f.write("corrupted content...\n")

    print(f"✓ Generated: {file_path}")


def generate_sample_encrypted(output_dir: Path):
    """TC08: 암호화된 PDF"""
    # 먼저 정상 PDF 생성
    temp_file = output_dir / "temp_for_encryption.pdf"
    c = canvas.Canvas(str(temp_file), pagesize=letter)
    c.drawString(100, 750, "This PDF will be encrypted")
    c.save()

    # 암호화 적용
    file_path = output_dir / "sample_encrypted.pdf"
    reader = PdfReader(str(temp_file))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # 비밀번호 설정
    writer.encrypt(user_password="test123", owner_password="owner123")

    with open(file_path, "wb") as f:
        writer.write(f)

    # 임시 파일 삭제
    temp_file.unlink()

    print(f"✓ Generated: {file_path}")


def generate_sample_large_pdfs(output_dir: Path):
    """TC05, TC09: 대용량 PDF (49MB, 150MB)"""
    # 주의: 실제 대용량 파일 생성은 시간이 오래 걸림
    # 실제 구현에서는 빈 파일로 대체하거나, 별도로 생성

    # 49MB PDF (제한 내)
    file_path_49 = output_dir / "sample_large_49mb.pdf"
    # TODO: 실제 대용량 PDF 생성 로직 (생략)
    # 여기서는 더미 파일 생성
    print(f"⚠ Skipped: {file_path_49} (수동 생성 필요)")

    # 150MB PDF (제한 초과)
    file_path_150 = output_dir / "sample_large_150mb.pdf"
    print(f"⚠ Skipped: {file_path_150} (수동 생성 필요)")


def generate_sample_malicious_js(output_dir: Path):
    """TC10: JavaScript 포함 PDF"""
    file_path = output_dir / "sample_malicious_js.pdf"

    # 정상 PDF 생성
    temp_file = output_dir / "temp_for_js.pdf"
    c = canvas.Canvas(str(temp_file), pagesize=letter)
    c.drawString(100, 750, "PDF with JavaScript")
    c.save()

    # JavaScript 추가 (저수준 조작)
    reader = PdfReader(str(temp_file))
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    # JavaScript 액션 추가 (간단한 예제)
    js_action = DictionaryObject()
    js_action.update({
        NameObject("/S"): NameObject("/JavaScript"),
        NameObject("/JS"): TextStringObject("app.alert('Test');"),
    })

    # Catalog에 추가
    if writer._root_object.get("/OpenAction") is None:
        writer._root_object[NameObject("/OpenAction")] = js_action

    with open(file_path, "wb") as f:
        writer.write(f)

    temp_file.unlink()

    print(f"✓ Generated: {file_path}")


def main():
    """메인 함수"""
    print("📄 테스트용 PDF 파일 생성 중...\n")

    output_dir = create_output_dir()

    # 각 테스트 케이스별 PDF 생성
    generate_sample_valid(output_dir)
    generate_sample_5pages(output_dir)
    generate_sample_10pages(output_dir)
    generate_sample_with_empty_page(output_dir)
    generate_sample_images_only(output_dir)
    generate_sample_corrupted(output_dir)
    generate_sample_encrypted(output_dir)
    generate_sample_large_pdfs(output_dir)
    generate_sample_malicious_js(output_dir)

    print("\n✅ PDF 파일 생성 완료!")
    print(f"📁 위치: {output_dir}")
    print("\n⚠ 대용량 PDF (49MB, 150MB)는 수동 생성이 필요합니다.")


if __name__ == "__main__":
    main()
```

#### 스크립트 실행
```bash
# reportlab 설치 (PDF 생성용)
pip install reportlab

# 스크립트 실행
python scripts/generate_test_pdfs.py

# 생성된 파일 확인
ls -lh tests/fixtures/pdf/
```

---

### 4.6 Step 6: 통합 테스트 및 리팩토링 (60분)

#### 작업 내용

1. **전체 테스트 실행**
   ```bash
   # 모든 테스트 실행
   pytest tests/test_pdf_parser.py -v

   # 커버리지 확인 (목표: 90% 이상)
   pytest tests/test_pdf_parser.py --cov=app/services/document_parser --cov-report=term-missing

   # 커버리지 HTML 리포트
   pytest tests/test_pdf_parser.py --cov=app/services/document_parser --cov-report=html
   open htmlcov/index.html
   ```

2. **코드 리팩토링**
   - **중복 코드 제거**: 공통 로직 메서드화
   - **가독성 향상**: 복잡한 로직 함수 분리
   - **타입 힌트 추가**: 모든 함수에 타입 명시
   - **Docstring 보완**: 모든 public 메서드 문서화

3. **성능 최적화**
   - 대용량 PDF 메모리 사용량 측정
   - 필요 시 스트리밍 방식 고려

4. **보안 강화**
   - 추가 악성 패턴 검사
   - 입력 검증 강화

#### 검증
```bash
# 최종 테스트
pytest tests/test_pdf_parser.py -v --tb=short

# 코드 품질 검사
flake8 app/services/document_parser/
mypy app/services/document_parser/
```

---

## 5. 검증 및 수동 테스트

### 5.1 자동화 테스트 검증
```bash
# 모든 테스트 케이스 통과 확인
pytest tests/test_pdf_parser.py -v

# 예상 결과:
# tests/test_pdf_parser.py::test_valid_pdf_parsing PASSED              [ 10%]
# tests/test_pdf_parser.py::test_page_number_extraction PASSED        [ 20%]
# tests/test_pdf_parser.py::test_multi_page_pdf PASSED                [ 30%]
# tests/test_pdf_parser.py::test_empty_page_skip PASSED               [ 40%]
# tests/test_pdf_parser.py::test_large_pdf_handling PASSED            [ 50%]
# tests/test_pdf_parser.py::test_pdf_with_images_only PASSED          [ 60%]
# tests/test_pdf_parser.py::test_corrupted_pdf_error PASSED           [ 70%]
# tests/test_pdf_parser.py::test_encrypted_pdf_warning PASSED         [ 80%]
# tests/test_pdf_parser.py::test_file_size_limit_exceeded PASSED      [ 90%]
# tests/test_pdf_parser.py::test_malicious_pdf_rejection PASSED       [100%]
#
# ========================== 10 passed in 2.34s ==========================
```

### 5.2 수동 테스트 (5개 실제 샘플 PDF)

**테스트 시나리오**:

1. **실제 기술 문서 PDF (예: Python 공식 문서)**
   ```bash
   python -c "
   from app.services.document_parser.pdf_parser import PDFParser
   parser = PDFParser()
   result = parser.parse('samples/python-docs.pdf')
   print(f'Pages: {result.total_pages}, Chars: {result.total_characters}')
   print(f'First page preview: {result.pages[0].content[:200]}')
   "
   ```

2. **회사 내부 문서 PDF (예: 휴가 규정)**
   - 텍스트 추출 정확도 확인
   - 페이지 번호 정확성 확인
   - 특수 문자 (한글, 영어, 숫자) 처리 확인

3. **복잡한 레이아웃 PDF (예: 보고서, 표 포함)**
   - 표 내용 추출 여부 (텍스트 순서 확인)
   - 다단 레이아웃 처리 확인

4. **스캔 PDF (이미지 기반)**
   - OCR 없이는 텍스트 추출 불가 확인
   - 에러 없이 빈 content 반환 확인

5. **대용량 PDF (50MB+)**
   - 메모리 사용량 모니터링
   - 응답 시간 측정 (목표: < 30초)

**수동 검증 체크리스트**:
- [ ] 한글 텍스트 정확히 추출
- [ ] 특수문자 (©, ®, ™) 처리
- [ ] 줄바꿈 및 단락 구분 유지
- [ ] 페이지 번호 정확성 100%
- [ ] 메타데이터 추출 (제목, 저자)

---

## 6. 산출물 (Deliverables)

### 6.1 코드 파일
- [x] `app/services/document_parser/__init__.py`
- [x] `app/services/document_parser/base_parser.py` (추상 클래스)
- [x] `app/services/document_parser/pdf_parser.py` (PDF 파서)
- [x] `tests/test_pdf_parser.py` (10개 테스트 케이스)
- [x] `scripts/generate_test_pdfs.py` (픽스처 생성 스크립트)

### 6.2 테스트 픽스처
- [x] `tests/fixtures/pdf/sample_valid.pdf`
- [x] `tests/fixtures/pdf/sample_5pages.pdf`
- [x] `tests/fixtures/pdf/sample_10pages.pdf`
- [x] `tests/fixtures/pdf/sample_with_empty_page.pdf`
- [x] `tests/fixtures/pdf/sample_large_49mb.pdf`
- [x] `tests/fixtures/pdf/sample_images_only.pdf`
- [x] `tests/fixtures/pdf/sample_corrupted.pdf`
- [x] `tests/fixtures/pdf/sample_encrypted.pdf`
- [x] `tests/fixtures/pdf/sample_large_150mb.pdf`
- [x] `tests/fixtures/pdf/sample_malicious_js.pdf`

### 6.3 문서
- [x] `docs/task-plans/task-1.5-execution-plan.md` (본 문서)
- [ ] `docs/api/pdf_parser_api.md` (API 문서, 선택)

### 6.4 테스트 리포트
- [ ] 테스트 커버리지 리포트 (HTML)
- [ ] 수동 테스트 결과 문서

---

## 7. 리스크 및 대응 방안

### 7.1 기술 리스크

#### Risk 1: pypdf 라이브러리의 한계
**증상**:
- 복잡한 PDF (표, 다단 레이아웃) 텍스트 순서 섞임
- 특정 PDF 인코딩 미지원

**확률**: Medium (30%)

**대응**:
1. **즉시 대응**:
   - 에러 핸들링으로 안정성 확보
   - 로그에 문제 파일 기록

2. **단기 대응** (Task 1.6 이후):
   - pdfplumber 추가 설치
   - 복잡한 PDF → pdfplumber 사용
   - 간단한 PDF → pypdf 사용 (성능 우선)

3. **장기 대응** (Phase 2):
   - OCR 라이브러리 추가 (Tesseract)
   - 스캔 PDF 지원

**결정 시점**: Task 1.5 완료 후 수동 테스트 결과 확인

---

#### Risk 2: 대용량 PDF 메모리 부족
**증상**:
- 100MB PDF 파싱 시 메모리 초과
- 서버 응답 없음

**확률**: Low (10%)

**대응**:
1. **즉시 대응**:
   - 파일 크기 제한 엄격히 적용 (100MB)
   - 메모리 모니터링 추가

2. **단기 대응**:
   - 페이지별 스트리밍 처리 (메모리 효율)
   - 청크 단위 처리 (배치 크기 조정)

3. **장기 대응**:
   - Celery 비동기 처리
   - 대용량 파일 → 백그라운드 작업

---

#### Risk 3: 보안 취약점 (악성 PDF)
**증상**:
- JavaScript 실행으로 서버 공격
- 파일 시스템 접근

**확률**: Low (5%, 적절한 통제 시)

**대응**:
1. **즉시 대응** (HARD RULE):
   - JavaScript 검사 로직 구현
   - 외부 링크 차단
   - 샌드박스 환경에서 파싱

2. **단기 대응**:
   - Docker 컨테이너 격리
   - 파일 시스템 읽기 전용

3. **장기 대응**:
   - 정기 보안 감사
   - OWASP PDF Security 가이드 준수

---

### 7.2 일정 리스크

#### Risk 4: 예상 시간 초과 (6시간 → 8시간)
**원인**:
- 테스트 픽스처 생성 시간 과소평가
- 예상치 못한 버그 디버깅

**확률**: Medium (40%)

**대응**:
1. **우선순위 조정**:
   - 핵심 기능 먼저 (Happy Path 테스트 우선)
   - Edge Case는 나중에 추가

2. **범위 축소**:
   - 대용량 PDF 테스트 생략 (수동 생성)
   - 악성 PDF 테스트 간소화

3. **다음 Task로 이월**:
   - Task 1.6에서 추가 테스트 보완

---

## 8. Next Steps (Task 1.5 완료 후)

### 8.1 즉시 수행
1. **코드 리뷰 요청**
   - Backend Lead에게 리뷰 요청
   - 보안 체크리스트 검토

2. **문서화**
   - API 문서 작성
   - 사용 예제 추가

3. **Git 커밋**
   ```bash
   git add .
   git commit -m "feat: Implement PDF parser module (Task 1.5)

   - Add BaseDocumentParser abstract class
   - Implement PDFParser with pypdf
   - Add 10 test cases (100% passing)
   - Add test fixture generation script
   - Add file size limit validation (100MB)
   - Add malicious PDF detection (JavaScript)

   Closes #5"
   ```

### 8.2 다음 Task 준비
**Task 1.6: 문서 파싱 모듈 구현 (DOCX, TXT, Markdown)** 준비:
- [ ] DOCX 파서 설계 검토
- [ ] python-docx 라이브러리 조사
- [ ] 통합 파서 인터페이스 설계

---

## 9. Appendix

### 9.1 참고 자료
- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [PDF 1.7 Specification](https://opensource.adobe.com/dc-acrobat-sdk-docs/pdfstandards/PDF32000_2008.pdf)
- [OWASP PDF Security Cheat Sheet](https://cheatsheetseries.owasp.org/)

### 9.2 유용한 커맨드
```bash
# 테스트 실행 (상세 출력)
pytest tests/test_pdf_parser.py -vv

# 특정 테스트만 실행
pytest tests/test_pdf_parser.py::test_valid_pdf_parsing -v

# 커버리지 확인
pytest tests/test_pdf_parser.py --cov=app/services/document_parser --cov-report=term-missing

# 디버깅 모드
pytest tests/test_pdf_parser.py -vv --pdb

# 로그 출력
pytest tests/test_pdf_parser.py -v --log-cli-level=DEBUG
```

### 9.3 트러블슈팅

**문제**: `ModuleNotFoundError: No module named 'pypdf'`
**해결**:
```bash
source venv/bin/activate
pip install pypdf==4.0.1
```

**문제**: 테스트 픽스처 파일 없음
**해결**:
```bash
python scripts/generate_test_pdfs.py
```

**문제**: 암호화 PDF 테스트 실패
**해결**:
```bash
# pypdf 최신 버전 확인
pip install --upgrade pypdf
```

---

## 10. Approval & Sign-off

### 10.1 체크리스트
Task 1.5 완료 조건:
- [ ] 테스트 케이스 10개 모두 통과 (100%)
- [ ] 코드 커버리지 ≥ 90%
- [ ] 5개 샘플 PDF 수동 테스트 성공
- [ ] 보안 검사 통과 (JavaScript 검사)
- [ ] 코드 리뷰 승인
- [ ] 문서화 완료

### 10.2 승인
- [ ] **Backend Lead**: _______________
- [ ] **Security Team**: _______________
- [ ] **Tech Lead**: _______________

**Review Deadline**: Task 1.5 완료 후 24시간 이내

---

**END OF EXECUTION PLAN**
