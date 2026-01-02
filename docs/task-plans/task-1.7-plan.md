# Task 1.7: 텍스트 청크 분할 로직 구현 - 실행 계획

---

## 📋 Meta

- **Task ID**: 1.7
- **Task명**: 텍스트 청크 분할 로직 구현
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-02
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
파싱된 문서 텍스트를 최적 크기의 청크(chunk)로 분할하여 벡터 임베딩 및 검색에 적합한 형태로 변환합니다. LangChain의 RecursiveCharacterTextSplitter를 사용하여 의미 단위를 유지하면서 분할합니다.

### 1.2 핵심 요구사항
- **기능**: 텍스트를 500자 단위로 분할, 50자 overlap
- **품질**: 청크 크기 평균 500자 ± 10%, 메타데이터 유지
- **성능**: 대용량 문서 처리 (10,000자 이상)
- **테스트**: 10개 테스트 케이스 100% 통과

### 1.3 성공 기준
- [ ] 청크 크기 검증 (평균 500자 ± 10%)
- [ ] Overlap 검증 (50자)
- [ ] 메타데이터 유지 확인 (document_id, chunk_index, document_title, page_number)
- [ ] 단위 테스트 통과 (10개 케이스)
- [ ] 대용량 문서 처리 성공 (10,000자+)

### 1.4 Why This Task Matters
**RAG 시스템의 핵심**:
- **검색 정확도**: 적절한 청크 크기가 검색 품질 결정
- **컨텍스트 유지**: Overlap으로 문맥 연속성 보장
- **임베딩 효율**: 토큰 제한(~125 토큰) 준수
- **확장성**: 모든 문서 타입에 재사용

---

## 2. 선행 조건 검증

### 2.1 환경 검증
실행 전 다음 사항을 확인합니다:

```bash
# Python 버전 확인 (3.11+ 필요)
python --version

# 가상환경 활성화 확인
which python  # venv 경로여야 함

# Task 1.6 완료 확인
ls -la app/services/document_parser/
```

### 2.2 의존성 확인
다음 Task들이 완료되어 있어야 합니다:

- [x] **Task 1.5**: PDF 파서 구현 완료
- [x] **Task 1.6**: DOCX, TXT, Markdown 파서 구현 완료

---

## 3. 기술 스택 선택

### 3.1 텍스트 분할 라이브러리 비교

| 라이브러리 | 장점 | 단점 | 선택 여부 |
|-----------|------|------|----------|
| **LangChain RecursiveCharacterTextSplitter** | - 의미 단위 분할<br>- Overlap 지원<br>- 다양한 구분자<br>- 메타데이터 유지 | - LangChain 의존성 | ⭐ **선택** |
| **tiktoken + 수동 분할** | - 정확한 토큰 수<br>- 의존성 적음 | - 복잡한 구현<br>- 의미 단위 무시 | 보류 |
| **spaCy + Sentence Split** | - 정확한 문장 분할 | - 무거움<br>- Overlap 구현 복잡 | 보류 |

### 3.2 최종 선택: **LangChain RecursiveCharacterTextSplitter**

**선택 이유**:
1. **의미 단위 보존**: 문장, 단락 경계 고려
2. **검증된 솔루션**: RAG 시스템 표준
3. **유연성**: 다양한 구분자 커스터마이징
4. **메타데이터 지원**: 청크별 메타데이터 자동 관리

**RecursiveCharacterTextSplitter 동작 원리**:
```
1차 시도: 단락 구분자 ("\n\n")로 분할
2차 시도: 문장 구분자 ("\n", ". ")로 분할
3차 시도: 단어 구분자 (" ")로 분할
4차 시도: 문자 단위로 분할 (최후 수단)
```

**Overlap의 중요성**:
- **문맥 보존**: 청크 경계에서 정보 손실 방지
- **검색 품질**: 관련 정보가 여러 청크에 분산되어도 검색 가능
- **예시**:
  ```
  Chunk 1: "...회사의 휴가 정책은 다음과 같습니다. 연차는..."
  Chunk 2: "연차는 입사 후 1년부터 15일 부여됩니다..."
  (Overlap: "연차는")
  ```

### 3.3 청크 크기 설정 근거

**chunk_size = 500자**:
- **토큰 변환**: 한글/영어 혼합 시 약 125 토큰
- **임베딩 모델**: nomic-embed-text 최대 토큰 ~512
- **검색 정확도**: 너무 크면 노이즈, 너무 작으면 컨텍스트 부족
- **LLM Context Window**: 충분한 여유 (5개 청크 = 625 토큰)

**chunk_overlap = 50자**:
- **Overlap 비율**: 10% (50/500)
- **문맥 보존**: 문장 1-2개 중복
- **저장 공간**: 증가 최소화

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 환경 설정 및 의존성 설치 (15분)

#### 작업 내용
1. **requirements.txt 업데이트**
   ```txt
   langchain==0.1.0
   langchain-text-splitters==0.0.1
   ```

2. **의존성 설치**
   ```bash
   source venv/bin/activate
   pip install langchain==0.1.0 langchain-text-splitters==0.0.1
   pip freeze > requirements.txt
   ```

3. **파일 생성**
   ```bash
   touch app/services/text_chunker.py
   touch tests/test_text_chunker.py
   ```

#### 검증
```bash
# LangChain 설치 확인
python -c "from langchain.text_splitter import RecursiveCharacterTextSplitter; print('OK')"
```

---

### 4.2 Step 2: 텍스트 청커 핵심 구현 (60분)

#### 작업 내용
`app/services/text_chunker.py` 작성

**설계 원칙**:
- **단일 책임**: 텍스트 분할만 담당
- **불변성**: 원본 문서 수정 안 함
- **타입 안전성**: Pydantic 모델 사용

```python
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.services.document_parser.base_parser import ParsedDocument, ParsedPage

logger = logging.getLogger(__name__)


class TextChunk(BaseModel):
    """텍스트 청크 데이터 모델"""

    chunk_index: int = Field(..., ge=0, description="청크 인덱스 (0부터 시작)")
    content: str = Field(..., min_length=1, description="청크 텍스트 내용")
    start_char: int = Field(..., ge=0, description="원본 텍스트에서 시작 위치")
    end_char: int = Field(..., ge=0, description="원본 텍스트에서 종료 위치")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="청크 메타데이터")

    class Config:
        frozen = False  # 메타데이터 업데이트 허용


class ChunkerConfig(BaseModel):
    """텍스트 청커 설정"""

    chunk_size: int = Field(default=500, ge=100, le=2000, description="청크 크기 (문자 수)")
    chunk_overlap: int = Field(default=50, ge=0, le=500, description="청크 Overlap (문자 수)")
    separators: List[str] = Field(
        default=["\n\n", "\n", ". ", " ", ""],
        description="분할 구분자 (우선순위 순서)"
    )
    keep_separator: bool = Field(default=True, description="구분자 유지 여부")


class DocumentChunker:
    """문서 텍스트 청크 분할기"""

    def __init__(self, config: Optional[ChunkerConfig] = None):
        """
        Args:
            config: 청커 설정 (기본값 사용 가능)
        """
        self.config = config or ChunkerConfig()

        # LangChain RecursiveCharacterTextSplitter 초기화
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=self.config.separators,
            keep_separator=self.config.keep_separator,
            length_function=len,  # 문자 수 기준
        )

        logger.info(
            f"DocumentChunker 초기화: chunk_size={self.config.chunk_size}, "
            f"overlap={self.config.chunk_overlap}"
        )

    def chunk_document(self, parsed_doc: ParsedDocument) -> List[TextChunk]:
        """
        파싱된 문서를 청크로 분할

        Args:
            parsed_doc: ParsedDocument (Task 1.5/1.6에서 생성)

        Returns:
            List[TextChunk]: 분할된 청크 리스트

        Raises:
            ValueError: 빈 문서인 경우
        """
        logger.info(
            f"문서 청킹 시작: {parsed_doc.total_pages}페이지, "
            f"{parsed_doc.total_characters}자"
        )

        if parsed_doc.total_characters == 0:
            logger.warning("빈 문서입니다. 청크 생성 불가.")
            return []

        # Step 1: 전체 텍스트 추출 (페이지별 구분 유지)
        full_text, page_boundaries = self._extract_full_text(parsed_doc)

        # Step 2: 텍스트 분할
        text_chunks = self.splitter.split_text(full_text)

        # Step 3: TextChunk 객체 생성 (메타데이터 포함)
        chunks = []
        current_pos = 0

        for idx, chunk_text in enumerate(text_chunks):
            # 청크의 원본 텍스트 위치 찾기
            start_pos = full_text.find(chunk_text, current_pos)
            if start_pos == -1:
                # Overlap으로 인해 중복된 경우, 이전 위치부터 재검색
                start_pos = current_pos
            end_pos = start_pos + len(chunk_text)

            # 청크가 속한 페이지 번호 결정
            page_number = self._find_page_number(start_pos, page_boundaries)

            # TextChunk 생성
            chunk = TextChunk(
                chunk_index=idx,
                content=chunk_text,
                start_char=start_pos,
                end_char=end_pos,
                metadata={
                    "page_number": page_number,
                    "document_title": parsed_doc.metadata.get("title", "Untitled"),
                    "total_chunks": len(text_chunks),  # 임시, 나중에 업데이트
                    "chunk_length": len(chunk_text),
                }
            )

            chunks.append(chunk)
            current_pos = start_pos + 1  # 다음 검색 위치

        # Step 4: total_chunks 업데이트
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk.metadata["total_chunks"] = total_chunks

        logger.info(f"문서 청킹 완료: {total_chunks}개 청크 생성")

        return chunks

    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        단순 텍스트 청킹 (ParsedDocument 없이)

        Args:
            text: 분할할 텍스트
            metadata: 추가 메타데이터 (선택)

        Returns:
            List[TextChunk]: 분할된 청크 리스트
        """
        if not text.strip():
            return []

        text_chunks = self.splitter.split_text(text)

        chunks = []
        current_pos = 0

        for idx, chunk_text in enumerate(text_chunks):
            start_pos = text.find(chunk_text, current_pos)
            if start_pos == -1:
                start_pos = current_pos
            end_pos = start_pos + len(chunk_text)

            chunk_metadata = metadata.copy() if metadata else {}
            chunk_metadata.update({
                "total_chunks": len(text_chunks),
                "chunk_length": len(chunk_text),
            })

            chunk = TextChunk(
                chunk_index=idx,
                content=chunk_text,
                start_char=start_pos,
                end_char=end_pos,
                metadata=chunk_metadata,
            )

            chunks.append(chunk)
            current_pos = start_pos + 1

        return chunks

    def _extract_full_text(
        self, parsed_doc: ParsedDocument
    ) -> tuple[str, List[tuple[int, int]]]:
        """
        ParsedDocument에서 전체 텍스트 추출 및 페이지 경계 계산

        Args:
            parsed_doc: ParsedDocument

        Returns:
            (full_text, page_boundaries)
            - full_text: 전체 텍스트 (페이지 구분자 포함)
            - page_boundaries: [(start_pos, page_number), ...]
        """
        full_text = ""
        page_boundaries = []
        current_pos = 0

        for page in parsed_doc.pages:
            page_text = page.content

            # 페이지 경계 기록
            page_boundaries.append((current_pos, page.page_number))

            # 텍스트 추가 (페이지 구분자로 "\n\n" 사용)
            full_text += page_text
            if page.page_number < parsed_doc.total_pages:
                full_text += "\n\n"  # 페이지 구분자

            current_pos = len(full_text)

        return full_text, page_boundaries

    def _find_page_number(
        self, char_position: int, page_boundaries: List[tuple[int, int]]
    ) -> int:
        """
        문자 위치로부터 페이지 번호 찾기

        Args:
            char_position: 문자 위치
            page_boundaries: 페이지 경계 리스트

        Returns:
            페이지 번호
        """
        for i in range(len(page_boundaries) - 1, -1, -1):
            boundary_pos, page_num = page_boundaries[i]
            if char_position >= boundary_pos:
                return page_num

        # 기본값: 첫 페이지
        return page_boundaries[0][1] if page_boundaries else 1

    def get_chunk_statistics(self, chunks: List[TextChunk]) -> Dict[str, Any]:
        """
        청크 통계 계산

        Args:
            chunks: 청크 리스트

        Returns:
            통계 딕셔너리
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0,
                "total_characters": 0,
            }

        chunk_sizes = [len(chunk.content) for chunk in chunks]

        return {
            "total_chunks": len(chunks),
            "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes),
            "min_chunk_size": min(chunk_sizes),
            "max_chunk_size": max(chunk_sizes),
            "total_characters": sum(chunk_sizes),
            "std_deviation": self._calculate_std(chunk_sizes),
        }

    @staticmethod
    def _calculate_std(values: List[float]) -> float:
        """표준 편차 계산"""
        if len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
```

---

### 4.3 Step 3: TDD - 테스트 케이스 작성 (60분)

#### 작업 내용
`tests/test_text_chunker.py` 작성 (10개 테스트 케이스)

```python
import pytest
from app.services.text_chunker import DocumentChunker, ChunkerConfig, TextChunk
from app.services.document_parser.base_parser import ParsedDocument, ParsedPage


@pytest.fixture
def default_chunker():
    """기본 설정 청커"""
    return DocumentChunker()


@pytest.fixture
def custom_chunker():
    """커스텀 설정 청커"""
    config = ChunkerConfig(chunk_size=300, chunk_overlap=30)
    return DocumentChunker(config=config)


@pytest.fixture
def sample_parsed_doc():
    """샘플 ParsedDocument"""
    page1 = ParsedPage(
        page_number=1,
        content="이것은 첫 번째 페이지입니다. " * 50,  # 약 600자
        metadata={}
    )
    page2 = ParsedPage(
        page_number=2,
        content="이것은 두 번째 페이지입니다. " * 50,  # 약 600자
        metadata={}
    )
    return ParsedDocument(
        pages=[page1, page2],
        total_pages=2,
        total_characters=1200,
        metadata={"title": "테스트 문서"}
    )


# ============================================
# Happy Path Tests (정상 시나리오)
# ============================================

def test_basic_chunking(default_chunker):
    """TC01: 기본 청킹 동작"""
    text = "This is a test. " * 100  # 약 1600자

    chunks = default_chunker.chunk_text(text)

    assert len(chunks) > 0
    assert all(isinstance(chunk, TextChunk) for chunk in chunks)
    assert chunks[0].chunk_index == 0


def test_chunk_size_constraint(default_chunker):
    """TC02: 청크 크기 제약 (평균 500자 ± 10%)"""
    text = "Lorem ipsum dolor sit amet. " * 200  # 약 5600자

    chunks = default_chunker.chunk_text(text)
    stats = default_chunker.get_chunk_statistics(chunks)

    avg_size = stats["avg_chunk_size"]
    assert 450 <= avg_size <= 550, f"평균 청크 크기: {avg_size} (목표: 450-550)"


def test_chunk_overlap(default_chunker):
    """TC03: Overlap 검증 (50자)"""
    # 명확한 구분이 있는 텍스트
    text = "Section A. " * 50 + "Section B. " * 50  # 약 1100자

    chunks = default_chunker.chunk_text(text)

    # 인접 청크 간 중복 확인
    if len(chunks) > 1:
        for i in range(len(chunks) - 1):
            chunk1_end = chunks[i].content[-50:]  # 마지막 50자
            chunk2_start = chunks[i + 1].content[:50]  # 처음 50자

            # 일부 중복이 있어야 함
            overlap_found = any(
                word in chunk2_start for word in chunk1_end.split()
            )
            assert overlap_found, f"청크 {i}와 {i+1} 사이에 overlap 없음"


def test_metadata_preservation(default_chunker, sample_parsed_doc):
    """TC04: 메타데이터 유지 확인"""
    chunks = default_chunker.chunk_document(sample_parsed_doc)

    for chunk in chunks:
        assert "page_number" in chunk.metadata
        assert "document_title" in chunk.metadata
        assert "total_chunks" in chunk.metadata
        assert "chunk_length" in chunk.metadata

        # document_title 확인
        assert chunk.metadata["document_title"] == "테스트 문서"


def test_page_number_tracking(default_chunker):
    """TC05: 페이지 번호 추적"""
    page1 = ParsedPage(page_number=1, content="A" * 600, metadata={})
    page2 = ParsedPage(page_number=2, content="B" * 600, metadata={})
    page3 = ParsedPage(page_number=3, content="C" * 600, metadata={})

    doc = ParsedDocument(
        pages=[page1, page2, page3],
        total_pages=3,
        total_characters=1800,
        metadata={}
    )

    chunks = default_chunker.chunk_document(doc)

    # 각 청크의 페이지 번호가 1, 2, 3 중 하나여야 함
    page_numbers = [chunk.metadata["page_number"] for chunk in chunks]
    assert all(1 <= pn <= 3 for pn in page_numbers)


# ============================================
# Edge Cases (경계 조건)
# ============================================

def test_empty_document(default_chunker):
    """TC06: 빈 문서 처리"""
    doc = ParsedDocument(
        pages=[],
        total_pages=0,
        total_characters=0,
        metadata={}
    )

    chunks = default_chunker.chunk_document(doc)

    assert chunks == []


def test_short_text(default_chunker):
    """TC07: 청크 크기보다 짧은 텍스트"""
    text = "Short text."  # 11자

    chunks = default_chunker.chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0].content == text


def test_exact_chunk_size(default_chunker):
    """TC08: 정확히 청크 크기인 텍스트"""
    text = "A" * 500  # 정확히 500자

    chunks = default_chunker.chunk_text(text)

    assert len(chunks) == 1
    assert len(chunks[0].content) == 500


def test_very_long_document(default_chunker):
    """TC09: 대용량 문서 (10,000자+)"""
    text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 200
    # 약 11,400자

    chunks = default_chunker.chunk_text(text)

    assert len(chunks) > 10  # 여러 청크로 분할
    stats = default_chunker.get_chunk_statistics(chunks)
    assert stats["total_characters"] >= 10000


# ============================================
# Configuration Tests (설정 테스트)
# ============================================

def test_custom_chunk_size(custom_chunker):
    """TC10: 커스텀 청크 크기 (300자)"""
    text = "Test text. " * 100  # 약 1100자

    chunks = custom_chunker.chunk_text(text)
    stats = custom_chunker.get_chunk_statistics(chunks)

    avg_size = stats["avg_chunk_size"]
    # 300자 ± 10%
    assert 270 <= avg_size <= 330, f"평균 청크 크기: {avg_size} (목표: 270-330)"


# ============================================
# Statistics Tests (통계 테스트)
# ============================================

def test_chunk_statistics(default_chunker):
    """TC11: 청크 통계 계산"""
    text = "Sample text. " * 150

    chunks = default_chunker.chunk_text(text)
    stats = default_chunker.get_chunk_statistics(chunks)

    assert "total_chunks" in stats
    assert "avg_chunk_size" in stats
    assert "min_chunk_size" in stats
    assert "max_chunk_size" in stats
    assert "total_characters" in stats
    assert "std_deviation" in stats

    assert stats["total_chunks"] == len(chunks)
    assert stats["avg_chunk_size"] > 0
```

---

### 4.4 Step 4: 통합 테스트 및 검증 (45분)

#### 작업 내용

1. **전체 테스트 실행**
   ```bash
   # 모든 테스트 실행
   pytest tests/test_text_chunker.py -v

   # 커버리지 확인 (목표: 95% 이상)
   pytest tests/test_text_chunker.py --cov=app/services/text_chunker --cov-report=term-missing
   ```

2. **실제 문서 통합 테스트**
   `tests/test_chunker_integration.py`:

   ```python
   import pytest
   from pathlib import Path
   from app.services.document_parser.factory import DocumentParserFactory
   from app.services.text_chunker import DocumentChunker


   def test_pdf_to_chunks_integration():
       """PDF → 파싱 → 청킹 통합 테스트"""
       pdf_path = "tests/fixtures/pdf/sample_valid.pdf"

       if not Path(pdf_path).exists():
           pytest.skip("PDF 파일 없음")

       # Step 1: PDF 파싱
       parser = DocumentParserFactory.create_parser(pdf_path)
       parsed_doc = parser.parse(pdf_path)

       # Step 2: 청킹
       chunker = DocumentChunker()
       chunks = chunker.chunk_document(parsed_doc)

       # Step 3: 검증
       assert len(chunks) > 0
       assert all(chunk.metadata["document_title"] for chunk in chunks)

       # 통계 출력
       stats = chunker.get_chunk_statistics(chunks)
       print(f"\n📊 청크 통계:")
       print(f"  - 총 청크 수: {stats['total_chunks']}")
       print(f"  - 평균 크기: {stats['avg_chunk_size']:.1f}자")
       print(f"  - 최소 크기: {stats['min_chunk_size']}자")
       print(f"  - 최대 크기: {stats['max_chunk_size']}자")


   def test_all_document_types_chunking():
       """모든 문서 타입 청킹 테스트"""
       test_files = [
           "tests/fixtures/pdf/sample_valid.pdf",
           "tests/fixtures/docx/sample_valid.docx",
           "tests/fixtures/txt/sample_valid.txt",
           "tests/fixtures/markdown/sample_valid.md",
       ]

       chunker = DocumentChunker()

       for file_path in test_files:
           if not Path(file_path).exists():
               continue

           # 파싱
           parser = DocumentParserFactory.create_parser(file_path)
           parsed_doc = parser.parse(file_path)

           # 청킹
           chunks = chunker.chunk_document(parsed_doc)

           assert len(chunks) > 0
           print(f"✓ {Path(file_path).name}: {len(chunks)} chunks")
   ```

3. **성능 테스트**
   ```python
   def test_large_document_performance():
       """대용량 문서 성능 테스트"""
       import time

       # 10,000자 문서 생성
       text = "Lorem ipsum dolor sit amet. " * 400

       chunker = DocumentChunker()

       start_time = time.time()
       chunks = chunker.chunk_text(text)
       elapsed = time.time() - start_time

       assert elapsed < 1.0, f"청킹 시간: {elapsed:.2f}초 (목표: < 1초)"
       print(f"\n⏱️  청킹 시간: {elapsed:.3f}초 ({len(chunks)} chunks)")
   ```

---

### 4.5 Step 5: 문서화 및 예제 작성 (30min)

#### 작업 내용

**README 업데이트** (`docs/api/text_chunker_usage.md`):

```markdown
# Text Chunker Usage Guide

## 개요
`DocumentChunker`는 파싱된 문서를 최적 크기의 청크로 분할합니다.

## 기본 사용법

### 1. ParsedDocument 청킹
```python
from app.services.document_parser.pdf_parser import PDFParser
from app.services.text_chunker import DocumentChunker

# PDF 파싱
parser = PDFParser()
parsed_doc = parser.parse("document.pdf")

# 청킹
chunker = DocumentChunker()
chunks = chunker.chunk_document(parsed_doc)

# 결과 확인
for chunk in chunks:
    print(f"Chunk {chunk.chunk_index}: {len(chunk.content)}자")
    print(f"  페이지: {chunk.metadata['page_number']}")
    print(f"  내용: {chunk.content[:100]}...")
```

### 2. 단순 텍스트 청킹
```python
from app.services.text_chunker import DocumentChunker

text = "긴 텍스트..."
chunker = DocumentChunker()
chunks = chunker.chunk_text(text, metadata={"source": "manual"})
```

### 3. 커스텀 설정
```python
from app.services.text_chunker import DocumentChunker, ChunkerConfig

config = ChunkerConfig(
    chunk_size=300,
    chunk_overlap=30,
    separators=["\n\n", "\n", " "]
)
chunker = DocumentChunker(config=config)
```

## 청크 통계
```python
stats = chunker.get_chunk_statistics(chunks)
print(f"평균 크기: {stats['avg_chunk_size']:.1f}자")
print(f"표준 편차: {stats['std_deviation']:.1f}자")
```

## 메타데이터 구조
각 청크는 다음 메타데이터를 포함합니다:
- `page_number`: 원본 페이지 번호
- `document_title`: 문서 제목
- `total_chunks`: 전체 청크 수
- `chunk_length`: 청크 길이
```

---

## 5. 검증 및 수동 테스트

### 5.1 자동화 테스트 검증
```bash
# 모든 테스트 실행
pytest tests/test_text_chunker.py -v

# 예상 결과:
# tests/test_text_chunker.py::test_basic_chunking PASSED              [  9%]
# tests/test_text_chunker.py::test_chunk_size_constraint PASSED      [ 18%]
# tests/test_text_chunker.py::test_chunk_overlap PASSED              [ 27%]
# tests/test_text_chunker.py::test_metadata_preservation PASSED      [ 36%]
# tests/test_text_chunker.py::test_page_number_tracking PASSED       [ 45%]
# tests/test_text_chunker.py::test_empty_document PASSED             [ 54%]
# tests/test_text_chunker.py::test_short_text PASSED                 [ 63%]
# tests/test_text_chunker.py::test_exact_chunk_size PASSED           [ 72%]
# tests/test_text_chunker.py::test_very_long_document PASSED         [ 81%]
# tests/test_text_chunker.py::test_custom_chunk_size PASSED          [ 90%]
# tests/test_text_chunker.py::test_chunk_statistics PASSED           [100%]
#
# ========================== 11 passed in 1.24s ==========================
```

### 5.2 수동 검증 체크리스트
- [ ] 청크 크기 평균 500자 ± 10% 확인
- [ ] 인접 청크 간 overlap 확인 (육안)
- [ ] 페이지 번호 정확성 확인
- [ ] 메타데이터 완전성 확인
- [ ] 대용량 문서 (10,000자+) 처리 성공
- [ ] 성능: 10,000자 문서 청킹 < 1초

---

## 6. 산출물 (Deliverables)

### 6.1 코드 파일
- [x] `app/services/text_chunker.py` (핵심 로직)
- [x] `tests/test_text_chunker.py` (11개 테스트 케이스)
- [x] `tests/test_chunker_integration.py` (통합 테스트)

### 6.2 문서
- [x] `docs/api/text_chunker_usage.md` (사용 가이드)

---

## 7. 리스크 및 대응 방안

### 7.1 기술 리스크

#### Risk 1: 청크 크기 불균형
**증상**:
- 일부 청크가 매우 크거나 작음
- 평균 500자 ± 10% 벗어남

**확률**: Medium (30%)

**대응**:
1. **즉시 대응**:
   - RecursiveCharacterTextSplitter의 separator 조정
   - 한글 문서: `["\n\n", "\n", ".", " "]` 순서 최적화

2. **단기 대응**:
   - 후처리 로직 추가 (너무 작은 청크 병합)
   - 청크 크기 동적 조정

---

#### Risk 2: 의미 단위 분리 (문장 중간 분할)
**증상**:
- 청크가 문장 중간에서 끊김
- 컨텍스트 손실

**확률**: Low (15%)

**대응**:
1. **즉시 대응**:
   - `keep_separator=True` 유지 (구분자 보존)
   - Overlap 50자로 문맥 보존

2. **단기 대응**:
   - spaCy 문장 분할기 추가 고려
   - 청크 경계를 문장 경계로 조정

---

#### Risk 3: 한글 토큰 변환 부정확
**증상**:
- 500자 ≠ 125 토큰 (예상과 다름)
- 임베딩 모델 토큰 제한 초과

**확률**: Medium (25%)

**대응**:
1. **즉시 대응**:
   - 500자 기준 유지 (안전 마진 확보)
   - 실제 토큰 수 측정 테스트

2. **단기 대응** (Task 1.8):
   - tiktoken 라이브러리로 실제 토큰 수 계산
   - 필요 시 chunk_size 조정 (500 → 450)

---

#### Risk 4: LangChain 의존성 버전 충돌
**증상**:
- RecursiveCharacterTextSplitter API 변경
- 설치 오류

**확률**: Low (10%)

**대응**:
1. **즉시 대응**:
   - 버전 고정: `langchain==0.1.0`
   - requirements.txt 명시

2. **장기 대응**:
   - LangChain 없이 자체 구현 고려

---

## 8. Next Steps (Task 1.7 완료 후)

### 8.1 즉시 수행
1. **코드 리뷰 요청**
   - Backend Lead에게 리뷰 요청
   - 청크 크기 전략 검토

2. **문서화**
   - API 문서 작성
   - 사용 예제 추가

3. **Git 커밋**
   ```bash
   git add .
   git commit -m "feat: Implement text chunking logic (Task 1.7)

   - Add DocumentChunker with LangChain RecursiveCharacterTextSplitter
   - Implement chunk_size=500, chunk_overlap=50 configuration
   - Add metadata tracking (page_number, document_title, chunk_index)
   - Add 11 comprehensive test cases (100% passing)
   - Add integration tests with all document parsers
   - Add chunk statistics calculation
   - Add performance test (<1s for 10k chars)

   Closes #7"
   ```

### 8.2 다음 Task 준비
**Task 1.8: 문서 임베딩 및 Milvus 저장** 준비:
- [ ] Ollama nomic-embed-text 모델 확인
- [ ] Milvus Collection 스키마 검토
- [ ] 배치 처리 전략 설계

---

## 9. Appendix

### 9.1 참고 자료
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [RecursiveCharacterTextSplitter API](https://api.python.langchain.com/en/latest/text_splitter/langchain.text_splitter.RecursiveCharacterTextSplitter.html)
- [RAG Chunking Strategies](https://www.pinecone.io/learn/chunking-strategies/)

### 9.2 청크 크기 설정 가이드

| 문서 타입 | 권장 chunk_size | 권장 overlap | 이유 |
|----------|----------------|--------------|------|
| 기술 문서 | 500-700 | 50-100 | 긴 설명, 예제 코드 포함 |
| 뉴스 기사 | 300-500 | 30-50 | 짧은 문장, 빠른 검색 |
| 법률 문서 | 700-1000 | 100-150 | 복잡한 문맥, 정확도 중요 |
| 채팅 로그 | 200-300 | 20-30 | 짧은 메시지, 빠른 응답 |

### 9.3 유용한 커맨드
```bash
# 특정 테스트만 실행
pytest tests/test_text_chunker.py::test_chunk_size_constraint -v

# 통합 테스트 실행
pytest tests/test_chunker_integration.py -v

# 커버리지 확인
pytest tests/test_text_chunker.py --cov=app/services/text_chunker --cov-report=html

# 성능 테스트
pytest tests/test_text_chunker.py::test_large_document_performance -v -s
```

### 9.4 트러블슈팅

**문제**: `ModuleNotFoundError: No module named 'langchain'`
**해결**:
```bash
source venv/bin/activate
pip install langchain==0.1.0 langchain-text-splitters==0.0.1
```

**문제**: 청크 크기가 너무 불균일함
**해결**:
```python
# separator 순서 조정
config = ChunkerConfig(
    separators=["\n\n", "\n", ". ", "。", " ", ""]  # 한글 마침표 추가
)
```

**문제**: Overlap이 제대로 동작하지 않음
**해결**:
```python
# keep_separator 확인
config = ChunkerConfig(
    chunk_overlap=50,
    keep_separator=True  # 구분자 유지 필수
)
```

---

## 10. Approval & Sign-off

### 10.1 체크리스트
Task 1.7 완료 조건:
- [ ] 청크 크기 평균 500자 ± 10% 달성
- [ ] Overlap 50자 검증 통과
- [ ] 메타데이터 유지 확인 (4개 필드)
- [ ] 단위 테스트 11개 모두 통과
- [ ] 통합 테스트 통과 (모든 문서 타입)
- [ ] 대용량 문서 처리 성공 (10,000자+)
- [ ] 성능 테스트 통과 (< 1초)
- [ ] 코드 커버리지 ≥ 95%
- [ ] 코드 리뷰 승인
- [ ] 문서화 완료

### 10.2 승인
- [ ] **Backend Lead**: _______________
- [ ] **Tech Lead**: _______________

**Review Deadline**: Task 1.7 완료 후 24시간 이내

---

**END OF EXECUTION PLAN**
