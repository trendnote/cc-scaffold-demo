# Task 1.6: 문서 파싱 모듈 구현 (DOCX, TXT, Markdown) - 실행 계획

---

## 📋 Meta

- **Task ID**: 1.6
- **Task명**: 문서 파싱 모듈 구현 (DOCX, TXT, Markdown)
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-02
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
DOCX, TXT, Markdown 문서에서 텍스트를 추출하고, 통합 파서 인터페이스를 통해 확장 가능한 문서 파싱 시스템을 구현합니다.

### 1.2 핵심 요구사항
- **기능**: DOCX, TXT, Markdown 파싱 + 통합 인터페이스
- **품질**: 각 타입별 3개 샘플 파싱 성공
- **보안**: [HARD RULE] 파일 타입 검증 (확장자 + MIME 타입)
- **확장성**: BaseDocumentParser 인터페이스로 새로운 파서 추가 용이

### 1.3 성공 기준
- [ ] DOCX 파싱 성공 (3개 샘플)
- [ ] TXT 파싱 성공 (3개 샘플)
- [ ] Markdown 파싱 성공 (3개 샘플)
- [ ] 잘못된 파일 타입 거부 확인
- [ ] 통합 테스트 통과

---

## 2. 선행 조건 검증

### 2.1 환경 검증
실행 전 다음 사항을 확인합니다:

```bash
# Python 버전 확인 (3.11+ 필요)
python --version

# 가상환경 활성화 확인
which python  # venv 경로여야 함

# Task 1.5 완료 확인
ls -la app/services/document_parser/base_parser.py
ls -la app/services/document_parser/pdf_parser.py
```

### 2.2 의존성 확인
다음 Task가 완료되어 있어야 합니다:

- [x] **Task 1.5**: PDF 파서 구현 완료 (BaseDocumentParser 추상 클래스 존재)

---

## 3. 기술 스택 선택

### 3.1 라이브러리 비교

#### DOCX 파서

| 라이브러리 | 장점 | 단점 | 선택 여부 |
|-----------|------|------|----------|
| **python-docx** | - 공식 라이브러리<br>- 안정적<br>- 문서 풍부 | - 복잡한 레이아웃 제한 | ⭐ **선택** |
| **docx2txt** | - 매우 가벼움<br>- 설치 간단 | - 기능 제한적<br>- 메타데이터 부족 | 보류 |

#### Markdown 파서

| 라이브러리 | 장점 | 단점 | 선택 여부 |
|-----------|------|------|----------|
| **Built-in (텍스트 읽기)** | - 의존성 없음<br>- 가장 빠름 | - 구조 파싱 없음 | ⭐ **선택** |
| **markdown** | - 구조 파싱<br>- HTML 변환 | - 복잡함<br>- 불필요한 기능 | 보류 |

**TXT 파서**: Built-in (표준 라이브러리만 사용)

### 3.2 최종 선택

**선택 이유**:
1. **단순성**: 텍스트 추출만 필요 (구조 파싱 불필요)
2. **안정성**: 검증된 라이브러리 사용
3. **확장성**: 나중에 고급 기능 추가 가능

**대체 전략**:
- Phase 2에서 복잡한 문서 처리 필요 시 라이브러리 추가 고려

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 환경 설정 및 의존성 설치 (20분)

#### 작업 내용
1. **requirements.txt 업데이트**
   ```txt
   python-docx==1.1.0
   python-magic==0.4.27  # MIME 타입 검증용
   ```

2. **의존성 설치**
   ```bash
   source venv/bin/activate
   pip install python-docx==1.1.0 python-magic==0.4.27
   pip freeze > requirements.txt
   ```

3. **디렉토리 구조 확인**
   ```bash
   # Task 1.5에서 이미 생성됨
   ls -la app/services/document_parser/

   # 새 파일 생성 준비
   touch app/services/document_parser/docx_parser.py
   touch app/services/document_parser/text_parser.py
   touch app/services/document_parser/markdown_parser.py
   touch app/services/document_parser/factory.py
   ```

#### 검증
```bash
# python-docx 설치 확인
python -c "import docx; print(docx.__version__)"  # 1.1.0

# python-magic 설치 확인
python -c "import magic; print('OK')"  # OK

# 디렉토리 구조 확인
tree app/services/document_parser
```

---

### 4.2 Step 2: BaseDocumentParser 확장 (30분)

#### 작업 내용
`app/services/document_parser/base_parser.py` 업데이트:

**추가 기능**:
- 파일 타입 검증 (MIME 타입)
- 파일 확장자 검증
- 공통 유틸리티 메서드

```python
# base_parser.py에 추가

import magic
from pathlib import Path
from typing import List


class UnsupportedFileTypeError(DocumentParserError):
    """지원하지 않는 파일 타입 에러"""
    pass


class BaseDocumentParser(ABC):
    """문서 파서 추상 클래스 (확장)"""

    # 지원하는 파일 확장자 (하위 클래스에서 오버라이드)
    SUPPORTED_EXTENSIONS: List[str] = []

    # 지원하는 MIME 타입 (하위 클래스에서 오버라이드)
    SUPPORTED_MIME_TYPES: List[str] = []

    def __init__(self, config: ParserConfig = None):
        self.config = config or ParserConfig()

    @abstractmethod
    def parse(self, file_path: str) -> ParsedDocument:
        """문서 파싱 (추상 메서드)"""
        pass

    def _validate_file_type(self, file_path: str) -> None:
        """
        파일 타입 검증 [HARD RULE]

        Args:
            file_path: 검증할 파일 경로

        Raises:
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
        """
        path = Path(file_path)

        # Step 1: 확장자 검증
        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"지원하지 않는 파일 확장자: {extension}. "
                f"지원하는 확장자: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        # Step 2: MIME 타입 검증
        try:
            mime_type = magic.from_file(file_path, mime=True)

            if mime_type not in self.SUPPORTED_MIME_TYPES:
                raise UnsupportedFileTypeError(
                    f"지원하지 않는 MIME 타입: {mime_type}. "
                    f"지원하는 타입: {', '.join(self.SUPPORTED_MIME_TYPES)}"
                )
        except Exception as e:
            # python-magic 실패 시 경고만 (확장자 검증으로 대체)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"MIME 타입 검증 실패 (확장자 검증으로 대체): {e}")

    def _validate_file_exists(self, file_path: str) -> None:
        """
        파일 존재 여부 확인

        Args:
            file_path: 확인할 파일 경로

        Raises:
            FileNotFoundError: 파일이 없을 때
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    def _validate_file_size(self, file_path: str) -> None:
        """파일 크기 검증 (Task 1.5에서 이미 구현)"""
        # 기존 코드 유지
        pass
```

#### 검증
```python
# tests/test_base_parser.py에 추가
def test_unsupported_file_type_error():
    """지원하지 않는 파일 타입 에러"""
    from app.services.document_parser.base_parser import UnsupportedFileTypeError

    error = UnsupportedFileTypeError("Test error")
    assert "Test error" in str(error)
```

---

### 4.3 Step 3: DOCX Parser 구현 (60분)

#### 작업 내용
`app/services/document_parser/docx_parser.py` 작성

**설계 원칙**:
- **단순성**: 텍스트만 추출 (표, 이미지 무시)
- **안정성**: 손상된 DOCX 처리
- **확장성**: 나중에 표 추출 기능 추가 가능

```python
import logging
from pathlib import Path
from typing import Dict, Any
from docx import Document
from docx.opc.exceptions import PackageNotFoundError

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    FileSizeLimitExceededError,
    CorruptedFileError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


class DOCXParser(BaseDocumentParser):
    """DOCX 문서 파서"""

    SUPPORTED_EXTENSIONS = [".docx"]
    SUPPORTED_MIME_TYPES = [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        DOCX 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: DOCX 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            CorruptedFileError: 손상된 파일
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
        """
        logger.info(f"DOCX 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        self._validate_file_exists(file_path)

        # Step 2: 파일 타입 검증 [HARD RULE]
        self._validate_file_type(file_path)

        # Step 3: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 4: DOCX 읽기
        try:
            doc = Document(file_path)
        except PackageNotFoundError as e:
            logger.error(f"DOCX 읽기 실패: {e}")
            raise CorruptedFileError(f"손상된 DOCX 파일입니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise CorruptedFileError(f"DOCX 파일을 읽을 수 없습니다: {e}")

        # Step 5: 단락별 텍스트 추출
        paragraphs = []
        total_characters = 0

        for para in doc.paragraphs:
            text = para.text.strip()

            # 빈 단락 건너뛰기
            if self.config.skip_empty_pages and not text:
                continue

            paragraphs.append(text)
            total_characters += len(text)

        # Step 6: 전체 텍스트 구성 (페이지 개념 없음)
        full_text = "\n\n".join(paragraphs)

        # DOCX는 페이지 번호 개념이 없으므로 전체를 1개 페이지로 처리
        page = ParsedPage(
            page_number=1,
            content=full_text,
            metadata={
                "paragraph_count": len(paragraphs),
                "format": "docx",
            }
        )

        # Step 7: 문서 메타데이터 추출
        metadata = self._extract_metadata(doc)

        # Step 8: 결과 반환
        result = ParsedDocument(
            pages=[page],
            total_pages=1,
            total_characters=total_characters,
            metadata=metadata,
        )

        logger.info(
            f"DOCX 파싱 완료: {file_path}, "
            f"단락 {len(paragraphs)}개, 문자 {total_characters}개"
        )

        return result

    def _extract_metadata(self, doc: Document) -> Dict[str, Any]:
        """
        DOCX 메타데이터 추출

        Args:
            doc: DOCX Document 객체

        Returns:
            메타데이터 딕셔너리
        """
        metadata = {}

        try:
            core_properties = doc.core_properties
            metadata = {
                "title": core_properties.title,
                "author": core_properties.author,
                "subject": core_properties.subject,
                "keywords": core_properties.keywords,
                "created": str(core_properties.created) if core_properties.created else None,
                "modified": str(core_properties.modified) if core_properties.modified else None,
            }
            # None 값 제거
            metadata = {k: v for k, v in metadata.items() if v is not None}
        except Exception as e:
            logger.warning(f"메타데이터 추출 실패: {e}")

        return metadata
```

#### 테스트 작성
`tests/test_docx_parser.py`:

```python
import pytest
from pathlib import Path
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.base_parser import (
    CorruptedFileError,
    UnsupportedFileTypeError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "docx"


@pytest.fixture
def docx_parser():
    return DOCXParser()


def test_valid_docx_parsing(docx_parser):
    """TC01: 정상 DOCX 파싱"""
    docx_path = FIXTURES_DIR / "sample_valid.docx"
    result = docx_parser.parse(str(docx_path))

    assert result.total_pages == 1
    assert len(result.pages) == 1
    assert result.total_characters > 0
    assert len(result.pages[0].content) > 0


def test_docx_with_tables(docx_parser):
    """TC02: 표 포함 DOCX (텍스트만 추출)"""
    docx_path = FIXTURES_DIR / "sample_with_table.docx"
    result = docx_parser.parse(str(docx_path))

    assert result.total_pages == 1
    assert result.total_characters > 0


def test_docx_metadata_extraction(docx_parser):
    """TC03: 메타데이터 추출"""
    docx_path = FIXTURES_DIR / "sample_with_metadata.docx"
    result = docx_parser.parse(str(docx_path))

    assert "title" in result.metadata or "author" in result.metadata


def test_invalid_file_type(docx_parser):
    """TC04: 잘못된 파일 타입 거부"""
    txt_path = FIXTURES_DIR / "fake.docx"  # 실제로는 TXT 파일

    with pytest.raises(UnsupportedFileTypeError):
        docx_parser.parse(str(txt_path))
```

---

### 4.4 Step 4: TXT Parser 구현 (30분)

#### 작업 내용
`app/services/document_parser/text_parser.py` 작성

```python
import logging
from pathlib import Path
from typing import Dict, Any

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    FileSizeLimitExceededError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


class TextParser(BaseDocumentParser):
    """TXT 문서 파서"""

    SUPPORTED_EXTENSIONS = [".txt"]
    SUPPORTED_MIME_TYPES = [
        "text/plain",
        "text/plain; charset=utf-8",
    ]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        TXT 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: TXT 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
        """
        logger.info(f"TXT 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        self._validate_file_exists(file_path)

        # Step 2: 파일 타입 검증 [HARD RULE]
        self._validate_file_type(file_path)

        # Step 3: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 4: TXT 읽기 (UTF-8 인코딩)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            logger.warning(f"UTF-8 디코딩 실패, 다른 인코딩 시도: {file_path}")
            try:
                with open(file_path, "r", encoding="cp949") as f:
                    content = f.read()
            except Exception as e:
                logger.error(f"TXT 읽기 실패: {e}")
                raise ValueError(f"텍스트 파일을 읽을 수 없습니다: {e}")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise ValueError(f"텍스트 파일을 읽을 수 없습니다: {e}")

        # Step 5: 페이지 구성 (전체를 1개 페이지로)
        page = ParsedPage(
            page_number=1,
            content=content,
            metadata={
                "format": "txt",
                "encoding": "utf-8",
            }
        )

        # Step 6: 결과 반환
        result = ParsedDocument(
            pages=[page],
            total_pages=1,
            total_characters=len(content),
            metadata={
                "filename": Path(file_path).name,
            },
        )

        logger.info(f"TXT 파싱 완료: {file_path}, 문자 {len(content)}개")

        return result
```

#### 테스트 작성
`tests/test_text_parser.py`:

```python
import pytest
from pathlib import Path
from app.services.document_parser.text_parser import TextParser

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "txt"


@pytest.fixture
def text_parser():
    return TextParser()


def test_valid_txt_parsing(text_parser):
    """TC01: 정상 TXT 파싱"""
    txt_path = FIXTURES_DIR / "sample_valid.txt"
    result = text_parser.parse(str(txt_path))

    assert result.total_pages == 1
    assert result.total_characters > 0


def test_utf8_encoding(text_parser):
    """TC02: UTF-8 인코딩 처리"""
    txt_path = FIXTURES_DIR / "sample_utf8.txt"
    result = text_parser.parse(str(txt_path))

    assert "한글" in result.pages[0].content or result.total_characters > 0


def test_empty_txt_file(text_parser):
    """TC03: 빈 TXT 파일"""
    txt_path = FIXTURES_DIR / "sample_empty.txt"
    result = text_parser.parse(str(txt_path))

    assert result.total_pages == 1
    assert result.total_characters == 0
```

---

### 4.5 Step 5: Markdown Parser 구현 (30분)

#### 작업 내용
`app/services/document_parser/markdown_parser.py` 작성

```python
import logging
from pathlib import Path
from typing import Dict, Any

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParsedDocument,
    ParsedPage,
    ParserConfig,
    FileSizeLimitExceededError,
    UnsupportedFileTypeError,
)

logger = logging.getLogger(__name__)


class MarkdownParser(BaseDocumentParser):
    """Markdown 문서 파서"""

    SUPPORTED_EXTENSIONS = [".md", ".markdown"]
    SUPPORTED_MIME_TYPES = [
        "text/markdown",
        "text/x-markdown",
        "text/plain",  # Markdown은 종종 text/plain으로 인식됨
    ]

    def parse(self, file_path: str) -> ParsedDocument:
        """
        Markdown 파일을 파싱하여 구조화된 데이터 반환

        Args:
            file_path: Markdown 파일 경로

        Returns:
            ParsedDocument: 파싱된 문서 데이터

        Raises:
            FileSizeLimitExceededError: 파일 크기 제한 초과
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
        """
        logger.info(f"Markdown 파싱 시작: {file_path}")

        # Step 1: 파일 존재 여부 확인
        self._validate_file_exists(file_path)

        # Step 2: 파일 타입 검증 [HARD RULE]
        self._validate_file_type(file_path)

        # Step 3: 파일 크기 검증 [HARD RULE]
        self._validate_file_size(file_path)

        # Step 4: Markdown 읽기 (UTF-8 인코딩)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 디코딩 실패: {file_path}")
            raise ValueError(f"Markdown 파일 인코딩 오류 (UTF-8 필요)")
        except Exception as e:
            logger.error(f"예상치 못한 에러: {e}")
            raise ValueError(f"Markdown 파일을 읽을 수 없습니다: {e}")

        # Step 5: 메타데이터 추출 (Front Matter 지원 - 선택적)
        metadata = self._extract_frontmatter(content)

        # Step 6: 페이지 구성 (전체를 1개 페이지로)
        page = ParsedPage(
            page_number=1,
            content=content,
            metadata={
                "format": "markdown",
                "has_frontmatter": bool(metadata),
            }
        )

        # Step 7: 결과 반환
        result = ParsedDocument(
            pages=[page],
            total_pages=1,
            total_characters=len(content),
            metadata=metadata,
        )

        logger.info(f"Markdown 파싱 완료: {file_path}, 문자 {len(content)}개")

        return result

    def _extract_frontmatter(self, content: str) -> Dict[str, Any]:
        """
        Markdown Front Matter 추출 (YAML 형식)

        Args:
            content: Markdown 내용

        Returns:
            Front Matter 딕셔너리
        """
        metadata = {}

        # Front Matter 형식: --- ... ---
        if content.startswith("---\n"):
            try:
                end_index = content.find("\n---\n", 4)
                if end_index != -1:
                    frontmatter = content[4:end_index]
                    # 간단한 파싱 (key: value 형식)
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Front Matter 파싱 실패: {e}")

        return metadata
```

#### 테스트 작성
`tests/test_markdown_parser.py`:

```python
import pytest
from pathlib import Path
from app.services.document_parser.markdown_parser import MarkdownParser

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "markdown"


@pytest.fixture
def markdown_parser():
    return MarkdownParser()


def test_valid_markdown_parsing(markdown_parser):
    """TC01: 정상 Markdown 파싱"""
    md_path = FIXTURES_DIR / "sample_valid.md"
    result = markdown_parser.parse(str(md_path))

    assert result.total_pages == 1
    assert result.total_characters > 0


def test_markdown_with_frontmatter(markdown_parser):
    """TC02: Front Matter 포함 Markdown"""
    md_path = FIXTURES_DIR / "sample_with_frontmatter.md"
    result = markdown_parser.parse(str(md_path))

    assert result.total_pages == 1
    assert len(result.metadata) > 0


def test_markdown_headers(markdown_parser):
    """TC03: 헤더 포함 Markdown"""
    md_path = FIXTURES_DIR / "sample_with_headers.md"
    result = markdown_parser.parse(str(md_path))

    content = result.pages[0].content
    assert "#" in content  # 헤더 마크다운 유지
```

---

### 4.6 Step 6: 파서 팩토리 패턴 구현 (30분)

#### 작업 내용
`app/services/document_parser/factory.py` 작성

**목적**: 파일 확장자에 따라 적절한 파서 자동 선택

```python
from pathlib import Path
from typing import Optional

from app.services.document_parser.base_parser import (
    BaseDocumentParser,
    ParserConfig,
    UnsupportedFileTypeError,
)
from app.services.document_parser.pdf_parser import PDFParser
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.text_parser import TextParser
from app.services.document_parser.markdown_parser import MarkdownParser


class DocumentParserFactory:
    """문서 파서 팩토리"""

    # 확장자별 파서 매핑
    PARSER_MAP = {
        ".pdf": PDFParser,
        ".docx": DOCXParser,
        ".txt": TextParser,
        ".md": MarkdownParser,
        ".markdown": MarkdownParser,
    }

    @classmethod
    def create_parser(
        cls,
        file_path: str,
        config: Optional[ParserConfig] = None
    ) -> BaseDocumentParser:
        """
        파일 확장자에 따라 적절한 파서 생성

        Args:
            file_path: 파싱할 파일 경로
            config: 파서 설정 (선택)

        Returns:
            BaseDocumentParser: 해당 파일 타입 파서

        Raises:
            UnsupportedFileTypeError: 지원하지 않는 파일 타입
        """
        extension = Path(file_path).suffix.lower()

        if extension not in cls.PARSER_MAP:
            raise UnsupportedFileTypeError(
                f"지원하지 않는 파일 확장자: {extension}. "
                f"지원하는 확장자: {', '.join(cls.PARSER_MAP.keys())}"
            )

        parser_class = cls.PARSER_MAP[extension]
        return parser_class(config=config)

    @classmethod
    def get_supported_extensions(cls) -> list[str]:
        """지원하는 파일 확장자 목록 반환"""
        return list(cls.PARSER_MAP.keys())
```

#### 테스트 작성
`tests/test_factory.py`:

```python
import pytest
from app.services.document_parser.factory import DocumentParserFactory
from app.services.document_parser.pdf_parser import PDFParser
from app.services.document_parser.docx_parser import DOCXParser
from app.services.document_parser.text_parser import TextParser
from app.services.document_parser.markdown_parser import MarkdownParser
from app.services.document_parser.base_parser import UnsupportedFileTypeError


def test_create_pdf_parser():
    """PDF 파서 생성"""
    parser = DocumentParserFactory.create_parser("test.pdf")
    assert isinstance(parser, PDFParser)


def test_create_docx_parser():
    """DOCX 파서 생성"""
    parser = DocumentParserFactory.create_parser("test.docx")
    assert isinstance(parser, DOCXParser)


def test_create_text_parser():
    """TXT 파서 생성"""
    parser = DocumentParserFactory.create_parser("test.txt")
    assert isinstance(parser, TextParser)


def test_create_markdown_parser():
    """Markdown 파서 생성"""
    parser = DocumentParserFactory.create_parser("test.md")
    assert isinstance(parser, MarkdownParser)


def test_unsupported_extension():
    """지원하지 않는 확장자"""
    with pytest.raises(UnsupportedFileTypeError):
        DocumentParserFactory.create_parser("test.xlsx")


def test_get_supported_extensions():
    """지원하는 확장자 목록"""
    extensions = DocumentParserFactory.get_supported_extensions()
    assert ".pdf" in extensions
    assert ".docx" in extensions
    assert ".txt" in extensions
    assert ".md" in extensions
```

---

### 4.7 Step 7: 테스트 픽스처 생성 (30분)

#### 작업 내용
`scripts/generate_test_documents.py` 작성

```python
#!/usr/bin/env python3
"""
테스트용 DOCX, TXT, Markdown 파일 생성 스크립트

Usage:
    python scripts/generate_test_documents.py
"""

import os
from pathlib import Path
from docx import Document


def create_output_dirs():
    """출력 디렉토리 생성"""
    dirs = [
        Path("tests/fixtures/docx"),
        Path("tests/fixtures/txt"),
        Path("tests/fixtures/markdown"),
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def generate_docx_samples(output_dir: Path):
    """DOCX 샘플 파일 생성"""

    # Sample 1: 기본 DOCX
    doc1 = Document()
    doc1.add_heading("Sample DOCX Document", 0)
    doc1.add_paragraph("This is a valid DOCX document for testing purposes.")
    doc1.add_paragraph("It contains multiple paragraphs.")
    doc1.save(output_dir / "sample_valid.docx")
    print(f"✓ Generated: {output_dir / 'sample_valid.docx'}")

    # Sample 2: 표 포함 DOCX
    doc2 = Document()
    doc2.add_heading("Document with Table", 0)
    doc2.add_paragraph("This document contains a table:")
    table = doc2.add_table(rows=3, cols=3)
    for i in range(3):
        for j in range(3):
            table.rows[i].cells[j].text = f"Cell {i},{j}"
    doc2.save(output_dir / "sample_with_table.docx")
    print(f"✓ Generated: {output_dir / 'sample_with_table.docx'}")

    # Sample 3: 메타데이터 포함 DOCX
    doc3 = Document()
    doc3.core_properties.title = "Test Document"
    doc3.core_properties.author = "Test Author"
    doc3.core_properties.subject = "Testing"
    doc3.add_heading("Document with Metadata", 0)
    doc3.add_paragraph("This document has metadata.")
    doc3.save(output_dir / "sample_with_metadata.docx")
    print(f"✓ Generated: {output_dir / 'sample_with_metadata.docx'}")


def generate_txt_samples(output_dir: Path):
    """TXT 샘플 파일 생성"""

    # Sample 1: 기본 TXT
    with open(output_dir / "sample_valid.txt", "w", encoding="utf-8") as f:
        f.write("Sample TXT Document\n")
        f.write("This is a valid text file for testing purposes.\n")
        f.write("It contains multiple lines.\n")
    print(f"✓ Generated: {output_dir / 'sample_valid.txt'}")

    # Sample 2: UTF-8 한글 포함
    with open(output_dir / "sample_utf8.txt", "w", encoding="utf-8") as f:
        f.write("한글 텍스트 파일\n")
        f.write("UTF-8 인코딩 테스트입니다.\n")
        f.write("English and 한글 mixed content.\n")
    print(f"✓ Generated: {output_dir / 'sample_utf8.txt'}")

    # Sample 3: 빈 파일
    with open(output_dir / "sample_empty.txt", "w", encoding="utf-8") as f:
        pass  # 빈 파일
    print(f"✓ Generated: {output_dir / 'sample_empty.txt'}")


def generate_markdown_samples(output_dir: Path):
    """Markdown 샘플 파일 생성"""

    # Sample 1: 기본 Markdown
    with open(output_dir / "sample_valid.md", "w", encoding="utf-8") as f:
        f.write("# Sample Markdown Document\n\n")
        f.write("This is a **valid** Markdown file for testing.\n\n")
        f.write("## Section 1\n\n")
        f.write("- Item 1\n")
        f.write("- Item 2\n")
    print(f"✓ Generated: {output_dir / 'sample_valid.md'}")

    # Sample 2: Front Matter 포함
    with open(output_dir / "sample_with_frontmatter.md", "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write("title: Test Document\n")
        f.write("author: Test Author\n")
        f.write("date: 2026-01-02\n")
        f.write("---\n\n")
        f.write("# Document with Front Matter\n\n")
        f.write("This Markdown file has YAML front matter.\n")
    print(f"✓ Generated: {output_dir / 'sample_with_frontmatter.md'}")

    # Sample 3: 헤더 포함
    with open(output_dir / "sample_with_headers.md", "w", encoding="utf-8") as f:
        f.write("# Level 1 Header\n\n")
        f.write("## Level 2 Header\n\n")
        f.write("### Level 3 Header\n\n")
        f.write("Content under headers.\n")
    print(f"✓ Generated: {output_dir / 'sample_with_headers.md'}")


def main():
    """메인 함수"""
    print("📄 테스트용 문서 파일 생성 중...\n")

    dirs = create_output_dirs()

    generate_docx_samples(dirs[0])
    generate_txt_samples(dirs[1])
    generate_markdown_samples(dirs[2])

    print("\n✅ 문서 파일 생성 완료!")
    print("📁 위치:")
    for d in dirs:
        print(f"  - {d}")


if __name__ == "__main__":
    main()
```

#### 스크립트 실행
```bash
# 스크립트 실행
python scripts/generate_test_documents.py

# 생성된 파일 확인
ls -lh tests/fixtures/docx/
ls -lh tests/fixtures/txt/
ls -lh tests/fixtures/markdown/
```

---

## 5. 통합 테스트 및 검증

### 5.1 전체 테스트 실행
```bash
# 모든 파서 테스트 실행
pytest tests/test_docx_parser.py -v
pytest tests/test_text_parser.py -v
pytest tests/test_markdown_parser.py -v
pytest tests/test_factory.py -v

# 통합 커버리지 확인
pytest tests/ --cov=app/services/document_parser --cov-report=html
```

### 5.2 통합 테스트 시나리오
`tests/test_integration.py`:

```python
import pytest
from pathlib import Path
from app.services.document_parser.factory import DocumentParserFactory


def test_parse_all_document_types():
    """모든 문서 타입 파싱 통합 테스트"""
    test_files = [
        "tests/fixtures/pdf/sample_valid.pdf",
        "tests/fixtures/docx/sample_valid.docx",
        "tests/fixtures/txt/sample_valid.txt",
        "tests/fixtures/markdown/sample_valid.md",
    ]

    for file_path in test_files:
        if Path(file_path).exists():
            parser = DocumentParserFactory.create_parser(file_path)
            result = parser.parse(file_path)

            assert result.total_pages >= 1
            assert result.total_characters >= 0
            print(f"✓ {Path(file_path).name}: {result.total_characters} chars")
```

### 5.3 수동 검증 체크리스트
- [ ] DOCX: 한글, 영어, 특수문자 정확히 추출
- [ ] TXT: UTF-8 인코딩 정상 처리
- [ ] Markdown: Front Matter 파싱 확인
- [ ] 파일 타입 검증: 잘못된 확장자 거부
- [ ] 파서 팩토리: 자동 파서 선택 정확성

---

## 6. 산출물 (Deliverables)

### 6.1 코드 파일
- [x] `app/services/document_parser/base_parser.py` (확장)
- [x] `app/services/document_parser/docx_parser.py`
- [x] `app/services/document_parser/text_parser.py`
- [x] `app/services/document_parser/markdown_parser.py`
- [x] `app/services/document_parser/factory.py`

### 6.2 테스트 파일
- [x] `tests/test_docx_parser.py`
- [x] `tests/test_text_parser.py`
- [x] `tests/test_markdown_parser.py`
- [x] `tests/test_factory.py`
- [x] `tests/test_integration.py`

### 6.3 테스트 픽스처
- [x] `tests/fixtures/docx/` (3개 샘플)
- [x] `tests/fixtures/txt/` (3개 샘플)
- [x] `tests/fixtures/markdown/` (3개 샘플)

### 6.4 스크립트
- [x] `scripts/generate_test_documents.py`

---

## 7. 리스크 및 대응 방안

### 7.1 기술 리스크

#### Risk 1: python-docx의 한계
**증상**:
- 복잡한 표 레이아웃 텍스트 순서 섞임
- 이미지 내 텍스트 추출 불가

**확률**: Medium (30%)

**대응**:
1. **즉시 대응**:
   - 텍스트만 추출 (표는 단순 텍스트로)
   - 에러 핸들링으로 안정성 확보

2. **단기 대응** (Phase 2):
   - 표 구조 파싱 추가 (python-docx table API)
   - OCR 라이브러리 추가 고려

---

#### Risk 2: 인코딩 문제 (TXT)
**증상**:
- UTF-8 외 인코딩 파일 읽기 실패
- 한글 깨짐

**확률**: Medium (25%)

**대응**:
1. **즉시 대응**:
   - UTF-8 실패 시 cp949 fallback
   - chardet 라이브러리로 자동 인코딩 감지

2. **장기 대응**:
   - 인코딩 자동 감지 로직 강화

---

#### Risk 3: MIME 타입 검증 실패
**증상**:
- python-magic 의존성 문제 (Windows)
- MIME 타입 오검출

**확률**: Low (15%)

**대응**:
1. **즉시 대응**:
   - MIME 검증 실패 시 확장자 검증으로 fallback
   - 경고 로그 출력

2. **단기 대응**:
   - 파일 시그니처 직접 검증 (magic number)

---

### 7.2 일정 리스크

#### Risk 4: 예상 시간 초과 (4시간 → 5시간)
**원인**:
- 테스트 픽스처 생성 시간
- 인코딩 이슈 디버깅

**확률**: Low (20%)

**대응**:
1. **우선순위 조정**:
   - 핵심 기능 먼저 (DOCX, TXT 우선)
   - Markdown은 시간 남을 때

2. **범위 축소**:
   - Front Matter 파싱 생략 가능

---

## 8. Next Steps (Task 1.6 완료 후)

### 8.1 즉시 수행
1. **코드 리뷰 요청**
   - Backend Lead에게 리뷰 요청
   - 보안 체크리스트 검토

2. **문서화**
   - API 문서 업데이트
   - 사용 예제 추가

3. **Git 커밋**
   ```bash
   git add .
   git commit -m "feat: Implement DOCX, TXT, Markdown parsers (Task 1.6)

   - Add DOCXParser with python-docx
   - Add TextParser with UTF-8 encoding support
   - Add MarkdownParser with front matter support
   - Add DocumentParserFactory for automatic parser selection
   - Add file type validation (extension + MIME type) [HARD RULE]
   - Add test fixtures generation script
   - Add integration tests

   Closes #6"
   ```

### 8.2 다음 Task 준비
**Task 1.7: 텍스트 청크 분할 로직 구현** 준비:
- [ ] LangChain RecursiveCharacterTextSplitter 조사
- [ ] 청크 크기 및 overlap 전략 검토
- [ ] 메타데이터 유지 설계

---

## 9. Appendix

### 9.1 참고 자료
- [python-docx Documentation](https://python-docx.readthedocs.io/)
- [python-magic Documentation](https://github.com/ahupp/python-magic)
- [Markdown Specification](https://spec.commonmark.org/)

### 9.2 유용한 커맨드
```bash
# 특정 파서 테스트만 실행
pytest tests/test_docx_parser.py::test_valid_docx_parsing -v

# 통합 테스트 실행
pytest tests/test_integration.py -v

# 커버리지 확인
pytest tests/ --cov=app/services/document_parser --cov-report=term-missing

# 로그 출력
pytest tests/test_docx_parser.py -v --log-cli-level=DEBUG
```

### 9.3 트러블슈팅

**문제**: `ModuleNotFoundError: No module named 'docx'`
**해결**:
```bash
source venv/bin/activate
pip install python-docx==1.1.0
```

**문제**: `ImportError: failed to find libmagic`
**해결** (macOS):
```bash
brew install libmagic
```

**해결** (Ubuntu):
```bash
sudo apt-get install libmagic1
```

**문제**: UTF-8 디코딩 에러
**해결**:
```bash
# chardet 라이브러리 설치
pip install chardet

# 파일 인코딩 확인
python -c "import chardet; print(chardet.detect(open('file.txt', 'rb').read()))"
```

---

## 10. Approval & Sign-off

### 10.1 체크리스트
Task 1.6 완료 조건:
- [ ] DOCX 파싱 성공 (3개 샘플)
- [ ] TXT 파싱 성공 (3개 샘플)
- [ ] Markdown 파싱 성공 (3개 샘플)
- [ ] 파일 타입 검증 통과 (확장자 + MIME)
- [ ] 파서 팩토리 정상 동작
- [ ] 통합 테스트 통과
- [ ] 코드 커버리지 ≥ 85%
- [ ] 코드 리뷰 승인
- [ ] 문서화 완료

### 10.2 승인
- [ ] **Backend Lead**: _______________
- [ ] **Tech Lead**: _______________

**Review Deadline**: Task 1.6 완료 후 24시간 이내

---

**END OF EXECUTION PLAN**
