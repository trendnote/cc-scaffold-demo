# Task 1.8: 문서 임베딩 및 Milvus 저장 - 실행 계획

---

## 📋 Meta

- **Task ID**: 1.8
- **Task명**: 문서 임베딩 및 Milvus 저장
- **예상 시간**: 6시간
- **담당**: Backend
- **작성일**: 2026-01-02
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
청크로 분할된 텍스트를 Ollama nomic-embed-text 모델로 임베딩하고, Milvus 벡터 데이터베이스와 PostgreSQL에 저장하여 **검색 가능한 인덱스**를 구축합니다. Phase 1의 최종 단계로 **전체 문서 처리 파이프라인 완성**이 목표입니다.

### 1.2 핵심 요구사항
- **기능**: 청크 임베딩 생성 → Milvus 저장 → PostgreSQL 메타데이터 저장
- **성능**: 배치 처리 (5개 문서 병렬), 재시도 로직 (3회)
- **안정성**: 에러 핸들링, 롤백, 트랜잭션 관리
- **검증**: 10개 테스트 문서 인덱싱 성공, 임베딩 차원 768 확인

### 1.3 성공 기준
- [ ] 10개 테스트 문서 인덱싱 성공
- [ ] Attu UI에서 벡터 확인 (768차원)
- [ ] PostgreSQL에 메타데이터 저장 확인
- [ ] 임베딩 차원 검증 (768차원)
- [ ] 배치 처리 정상 동작 (5개 병렬)
- [ ] 재시도 로직 동작 확인
- [ ] 롤백 메커니즘 검증

### 1.4 Why This Task Matters
**RAG 시스템의 핵심 완성**:
- **검색 가능성**: 벡터 임베딩 → 의미 기반 검색
- **전체 파이프라인 연결**: 파싱 → 청킹 → 임베딩 → 저장
- **Phase 2 준비**: 검색 API 구현 기반 마련
- **데이터 무결성**: PostgreSQL + Milvus 이중 저장

---

## 2. 선행 조건 검증

### 2.1 환경 검증
실행 전 다음 사항을 확인합니다:

```bash
# Python 버전 확인 (3.11+ 필요)
python --version

# 가상환경 활성화 확인
which python  # venv 경로여야 함

# Task 1.1-1.7 완료 확인
ls -la app/services/document_parser/
ls -la app/services/text_chunker.py
ls -la app/db/milvus_client.py
ls -la app/models/

# Docker 컨테이너 상태 확인
docker ps | grep milvus
docker ps | grep postgres
docker ps | grep ollama
```

### 2.2 서비스 확인
```bash
# Milvus 연결 확인
python -c "from pymilvus import connections; connections.connect('default', host='localhost', port='19530'); print('Milvus OK')"

# PostgreSQL 연결 확인
psql -h localhost -U postgres -d rag_platform -c "SELECT 1;"

# Ollama 모델 확인
docker exec -it ollama ollama list | grep nomic-embed-text
```

### 2.3 의존성 확인
다음 Task들이 완료되어 있어야 합니다:

- [x] **Task 1.3**: Milvus Collection 생성 완료
- [x] **Task 1.4**: Ollama nomic-embed-text 모델 다운로드 완료
- [x] **Task 1.5**: PDF 파서 구현 완료
- [x] **Task 1.6**: DOCX, TXT, Markdown 파서 구현 완료
- [x] **Task 1.7**: 텍스트 청커 구현 완료
- [x] **Task 1.2**: PostgreSQL 스키마 및 Documents 테이블 생성 완료

---

## 3. 기술 스택 선택

### 3.1 임베딩 모델 선택

| 모델 | 차원 | 장점 | 단점 | 선택 여부 |
|------|------|------|------|----------|
| **nomic-embed-text** | 768 | - 로컬 실행<br>- 빠름<br>- 비용 없음 | - OpenAI보다 품질 낮음 | ⭐ **선택** (Phase 1) |
| **OpenAI text-embedding-3-small** | 1536 | - 높은 품질<br>- 안정적 | - 비용 발생<br>- API 의존 | 보류 (Phase 2) |
| **OpenAI text-embedding-3-large** | 3072 | - 최고 품질 | - 비용 높음<br>- 느림 | 보류 |

### 3.2 최종 선택: **nomic-embed-text** (Ollama)

**선택 이유**:
1. **로컬 실행**: 외부 API 의존성 없음
2. **비용 효율**: 무료
3. **성능**: 로컬에서 빠른 응답 (GPU 사용 시)
4. **검증 후 전환 가능**: Task 2.5a에서 품질 평가 후 OpenAI 전환 가능

**nomic-embed-text 스펙**:
- **차원**: 768
- **최대 입력**: 8192 토큰
- **속도**: ~50ms per chunk (GPU), ~200ms (CPU)
- **품질**: Retrieval 작업에 최적화

### 3.3 배치 처리 전략

**왜 배치 처리?**
- **성능**: 5개 문서 병렬 처리 → 5배 빠름
- **안정성**: 1개 실패해도 나머지 계속 진행
- **리소스 효율**: Ollama 동시 요청 처리

**배치 크기: 5**
- **근거**: Ollama 기본 동시 처리 제한 (~4-8)
- **메모리**: 5 chunks × 768 dim × 4 bytes ≈ 15KB (충분히 작음)
- **에러율**: 실패 시 재시도 가능한 크기

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 환경 설정 및 의존성 설치 (20분)

#### 작업 내용
1. **requirements.txt 업데이트**
   ```txt
   langchain-community==0.0.20
   ollama==0.1.6
   tenacity==8.2.3  # 재시도 로직용
   ```

2. **의존성 설치**
   ```bash
   source venv/bin/activate
   pip install langchain-community==0.0.20 ollama==0.1.6 tenacity==8.2.3
   pip freeze > requirements.txt
   ```

3. **파일 생성**
   ```bash
   touch app/services/document_indexer.py
   touch app/services/embedding_service.py
   touch tests/test_document_indexer.py
   touch tests/test_embedding_service.py
   ```

#### 검증
```bash
# Ollama Python 클라이언트 확인
python -c "import ollama; print(ollama.__version__)"

# tenacity 확인
python -c "from tenacity import retry; print('OK')"
```

---

### 4.2 Step 2: 임베딩 서비스 구현 (60분)

#### 작업 내용
`app/services/embedding_service.py` 작성

**설계 원칙**:
- **단일 책임**: 임베딩 생성만 담당
- **재시도 로직**: 네트워크 오류 대응
- **타입 안전성**: 입출력 타입 명시

```python
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
import ollama
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class EmbeddingConfig(BaseModel):
    """임베딩 서비스 설정"""

    model_name: str = Field(default="nomic-embed-text", description="임베딩 모델명")
    expected_dimension: int = Field(default=768, description="예상 임베딩 차원")
    batch_size: int = Field(default=5, ge=1, le=20, description="배치 크기")
    max_retries: int = Field(default=3, ge=1, le=10, description="최대 재시도 횟수")


class EmbeddingServiceError(Exception):
    """임베딩 서비스 기본 에러"""
    pass


class EmbeddingDimensionError(EmbeddingServiceError):
    """임베딩 차원 불일치 에러"""
    pass


class OllamaEmbeddingService:
    """Ollama 임베딩 서비스"""

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Args:
            config: 임베딩 설정
        """
        self.config = config or EmbeddingConfig()
        self.client = ollama.Client()

        logger.info(
            f"OllamaEmbeddingService 초기화: model={self.config.model_name}, "
            f"dimension={self.config.expected_dimension}"
        )

        # 모델 존재 여부 확인
        self._verify_model_exists()

    def _verify_model_exists(self) -> None:
        """
        Ollama 모델 존재 여부 확인

        Raises:
            EmbeddingServiceError: 모델이 없을 때
        """
        try:
            models = self.client.list()
            model_names = [model["name"] for model in models.get("models", [])]

            if self.config.model_name not in model_names:
                raise EmbeddingServiceError(
                    f"Ollama 모델 '{self.config.model_name}'이 없습니다. "
                    f"다음 명령으로 다운로드하세요: "
                    f"ollama pull {self.config.model_name}"
                )

            logger.info(f"Ollama 모델 '{self.config.model_name}' 확인 완료")

        except Exception as e:
            logger.error(f"Ollama 연결 실패: {e}")
            raise EmbeddingServiceError(f"Ollama 연결 실패: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def embed_text(self, text: str) -> List[float]:
        """
        단일 텍스트 임베딩 생성 (재시도 로직 포함)

        Args:
            text: 임베딩할 텍스트

        Returns:
            List[float]: 임베딩 벡터 (768차원)

        Raises:
            EmbeddingServiceError: 임베딩 생성 실패
            EmbeddingDimensionError: 차원 불일치
        """
        if not text.strip():
            logger.warning("빈 텍스트 입력, 0 벡터 반환")
            return [0.0] * self.config.expected_dimension

        try:
            response = self.client.embeddings(
                model=self.config.model_name,
                prompt=text
            )

            embedding = response["embedding"]

            # 차원 검증
            if len(embedding) != self.config.expected_dimension:
                raise EmbeddingDimensionError(
                    f"임베딩 차원 불일치: {len(embedding)} "
                    f"(예상: {self.config.expected_dimension})"
                )

            return embedding

        except EmbeddingDimensionError:
            raise
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise EmbeddingServiceError(f"임베딩 생성 실패: {e}")

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        배치 텍스트 임베딩 생성

        Args:
            texts: 텍스트 리스트

        Returns:
            List[List[float]]: 임베딩 벡터 리스트

        Raises:
            EmbeddingServiceError: 임베딩 생성 실패
        """
        if not texts:
            return []

        logger.info(f"배치 임베딩 생성 시작: {len(texts)}개 텍스트")

        embeddings = []
        failed_indices = []

        for idx, text in enumerate(texts):
            try:
                embedding = self.embed_text(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(f"텍스트 {idx} 임베딩 실패: {e}")
                failed_indices.append(idx)
                # 실패한 경우 0 벡터로 대체
                embeddings.append([0.0] * self.config.expected_dimension)

        if failed_indices:
            logger.warning(
                f"배치 임베딩 중 {len(failed_indices)}개 실패: {failed_indices}"
            )

        logger.info(f"배치 임베딩 완료: {len(embeddings)}개 생성")

        return embeddings

    def get_embedding_dimension(self) -> int:
        """임베딩 차원 반환"""
        return self.config.expected_dimension
```

#### 테스트 작성
`tests/test_embedding_service.py`:

```python
import pytest
from app.services.embedding_service import (
    OllamaEmbeddingService,
    EmbeddingConfig,
    EmbeddingServiceError,
    EmbeddingDimensionError,
)


@pytest.fixture
def embedding_service():
    """기본 임베딩 서비스"""
    return OllamaEmbeddingService()


def test_embed_single_text(embedding_service):
    """TC01: 단일 텍스트 임베딩"""
    text = "This is a test sentence for embedding."

    embedding = embedding_service.embed_text(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)


def test_embed_korean_text(embedding_service):
    """TC02: 한글 텍스트 임베딩"""
    text = "이것은 한글 텍스트 임베딩 테스트입니다."

    embedding = embedding_service.embed_text(text)

    assert len(embedding) == 768


def test_embed_empty_text(embedding_service):
    """TC03: 빈 텍스트 처리"""
    text = ""

    embedding = embedding_service.embed_text(text)

    # 0 벡터 반환
    assert len(embedding) == 768
    assert all(x == 0.0 for x in embedding)


def test_embed_batch(embedding_service):
    """TC04: 배치 임베딩"""
    texts = [
        "First sentence.",
        "Second sentence.",
        "Third sentence.",
    ]

    embeddings = embedding_service.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == 768 for emb in embeddings)


def test_embedding_dimension(embedding_service):
    """TC05: 임베딩 차원 확인"""
    dimension = embedding_service.get_embedding_dimension()

    assert dimension == 768
```

---

### 4.3 Step 3: Document Indexer 구현 (120min)

#### 작업 내용
`app/services/document_indexer.py` 작성

**설계 원칙**:
- **트랜잭션**: PostgreSQL + Milvus 원자성
- **롤백**: 실패 시 이전 상태 복구
- **배치 처리**: 5개 문서 병렬

```python
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from pymilvus import Collection, utility

from app.services.document_parser.factory import DocumentParserFactory
from app.services.text_chunker import DocumentChunker
from app.services.embedding_service import OllamaEmbeddingService
from app.db.milvus_client import get_milvus_collection
from app.models.document import Document  # SQLAlchemy 모델
from app.db.session import get_db

logger = logging.getLogger(__name__)


class IndexingResult(BaseModel):
    """인덱싱 결과"""

    success: bool = Field(..., description="성공 여부")
    document_id: Optional[int] = Field(None, description="문서 ID (성공 시)")
    file_path: str = Field(..., description="파일 경로")
    total_chunks: int = Field(default=0, description="생성된 청크 수")
    indexed_chunks: int = Field(default=0, description="인덱싱된 청크 수")
    error_message: Optional[str] = Field(None, description="에러 메시지 (실패 시)")
    processing_time_ms: int = Field(..., description="처리 시간 (밀리초)")


class DocumentIndexerConfig(BaseModel):
    """문서 인덱서 설정"""

    batch_size: int = Field(default=5, ge=1, le=20, description="배치 크기")
    max_retries: int = Field(default=3, ge=1, le=10, description="최대 재시도")
    collection_name: str = Field(default="documents", description="Milvus Collection명")


class DocumentIndexer:
    """문서 인덱서 (파싱 → 청킹 → 임베딩 → 저장)"""

    def __init__(
        self,
        db_session: Session,
        config: Optional[DocumentIndexerConfig] = None
    ):
        """
        Args:
            db_session: SQLAlchemy 세션
            config: 인덱서 설정
        """
        self.db = db_session
        self.config = config or DocumentIndexerConfig()

        # 서비스 초기화
        self.chunker = DocumentChunker()
        self.embedding_service = OllamaEmbeddingService()

        # Milvus Collection
        self.collection = get_milvus_collection(self.config.collection_name)

        logger.info(
            f"DocumentIndexer 초기화: batch_size={self.config.batch_size}"
        )

    def index_document(self, file_path: str) -> IndexingResult:
        """
        단일 문서 인덱싱 (전체 파이프라인)

        Args:
            file_path: 문서 파일 경로

        Returns:
            IndexingResult: 인덱싱 결과
        """
        import time
        start_time = time.time()

        logger.info(f"문서 인덱싱 시작: {file_path}")

        try:
            # Step 1: 문서 파싱
            parser = DocumentParserFactory.create_parser(file_path)
            parsed_doc = parser.parse(file_path)

            logger.info(
                f"파싱 완료: {parsed_doc.total_pages}페이지, "
                f"{parsed_doc.total_characters}자"
            )

            # Step 2: 청킹
            chunks = self.chunker.chunk_document(parsed_doc)

            logger.info(f"청킹 완료: {len(chunks)}개 청크")

            if not chunks:
                raise ValueError("청크가 생성되지 않았습니다 (빈 문서)")

            # Step 3: PostgreSQL에 문서 메타데이터 저장
            document = self._save_document_metadata(file_path, parsed_doc)

            logger.info(f"문서 메타데이터 저장 완료: document_id={document.id}")

            # Step 4: 임베딩 생성
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.embed_batch(chunk_texts)

            logger.info(f"임베딩 생성 완료: {len(embeddings)}개")

            # Step 5: Milvus에 저장
            indexed_count = self._save_to_milvus(
                document_id=document.id,
                chunks=chunks,
                embeddings=embeddings,
                parsed_doc=parsed_doc
            )

            logger.info(f"Milvus 저장 완료: {indexed_count}개 청크")

            # Step 6: 문서 상태 업데이트
            document.indexed_at = datetime.utcnow()
            document.chunk_count = indexed_count
            self.db.commit()

            # 결과 반환
            processing_time_ms = int((time.time() - start_time) * 1000)

            return IndexingResult(
                success=True,
                document_id=document.id,
                file_path=file_path,
                total_chunks=len(chunks),
                indexed_chunks=indexed_count,
                processing_time_ms=processing_time_ms
            )

        except Exception as e:
            logger.error(f"문서 인덱싱 실패: {e}", exc_info=True)
            self.db.rollback()

            processing_time_ms = int((time.time() - start_time) * 1000)

            return IndexingResult(
                success=False,
                file_path=file_path,
                error_message=str(e),
                processing_time_ms=processing_time_ms
            )

    def index_batch(self, file_paths: List[str]) -> List[IndexingResult]:
        """
        배치 문서 인덱싱

        Args:
            file_paths: 파일 경로 리스트

        Returns:
            List[IndexingResult]: 인덱싱 결과 리스트
        """
        logger.info(f"배치 인덱싱 시작: {len(file_paths)}개 문서")

        results = []

        # 배치 크기로 분할
        for i in range(0, len(file_paths), self.config.batch_size):
            batch = file_paths[i:i + self.config.batch_size]

            logger.info(f"배치 {i // self.config.batch_size + 1} 처리 중...")

            for file_path in batch:
                result = self.index_document(file_path)
                results.append(result)

        # 통계
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count

        logger.info(
            f"배치 인덱싱 완료: 성공 {success_count}, 실패 {fail_count}"
        )

        return results

    def _save_document_metadata(
        self, file_path: str, parsed_doc: Any
    ) -> Document:
        """
        PostgreSQL에 문서 메타데이터 저장

        Args:
            file_path: 파일 경로
            parsed_doc: 파싱된 문서

        Returns:
            Document: SQLAlchemy 모델
        """
        import os
        from pathlib import Path

        document = Document(
            title=parsed_doc.metadata.get("title") or Path(file_path).stem,
            file_path=file_path,
            file_type=Path(file_path).suffix.lower(),
            file_size=os.path.getsize(file_path),
            total_pages=parsed_doc.total_pages,
            total_characters=parsed_doc.total_characters,
            metadata=parsed_doc.metadata,
            created_at=datetime.utcnow(),
        )

        self.db.add(document)
        self.db.flush()  # ID 생성 (commit 전)

        return document

    def _save_to_milvus(
        self,
        document_id: int,
        chunks: List[Any],
        embeddings: List[List[float]],
        parsed_doc: Any
    ) -> int:
        """
        Milvus에 벡터 + 메타데이터 저장

        Args:
            document_id: 문서 ID
            chunks: TextChunk 리스트
            embeddings: 임베딩 벡터 리스트
            parsed_doc: 파싱된 문서

        Returns:
            int: 저장된 청크 수

        Raises:
            Exception: Milvus 저장 실패
        """
        # Milvus 엔티티 구성
        entities = []

        for chunk, embedding in zip(chunks, embeddings):
            entity = {
                "document_id": document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "embedding": embedding,
                "page_number": chunk.metadata.get("page_number", 1),
                "metadata": {
                    "document_title": chunk.metadata.get("document_title", ""),
                    "chunk_length": chunk.metadata.get("chunk_length", 0),
                    "total_chunks": chunk.metadata.get("total_chunks", 0),
                }
            }
            entities.append(entity)

        # Milvus에 삽입
        try:
            # Collection에 맞는 형식으로 변환
            insert_data = [
                [e["document_id"] for e in entities],
                [e["chunk_index"] for e in entities],
                [e["content"] for e in entities],
                [e["embedding"] for e in entities],
                [e["page_number"] for e in entities],
                [e["metadata"] for e in entities],
            ]

            self.collection.insert(insert_data)
            self.collection.flush()

            logger.info(f"Milvus에 {len(entities)}개 엔티티 저장 완료")

            return len(entities)

        except Exception as e:
            logger.error(f"Milvus 저장 실패: {e}")
            raise

    def delete_document(self, document_id: int) -> bool:
        """
        문서 삭제 (PostgreSQL + Milvus)

        Args:
            document_id: 문서 ID

        Returns:
            bool: 성공 여부
        """
        try:
            # Step 1: Milvus에서 삭제
            expr = f"document_id == {document_id}"
            self.collection.delete(expr)
            self.collection.flush()

            logger.info(f"Milvus에서 document_id={document_id} 삭제 완료")

            # Step 2: PostgreSQL에서 삭제
            document = self.db.query(Document).filter(
                Document.id == document_id
            ).first()

            if document:
                self.db.delete(document)
                self.db.commit()

                logger.info(f"PostgreSQL에서 document_id={document_id} 삭제 완료")

            return True

        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            self.db.rollback()
            return False
```

---

### 4.4 Step 4: 통합 테스트 작성 (60min)

#### 작업 내용
`tests/test_document_indexer.py`:

```python
import pytest
from pathlib import Path
from sqlalchemy.orm import Session
from app.services.document_indexer import DocumentIndexer, IndexingResult
from app.db.session import get_db
from app.models.document import Document


@pytest.fixture
def db_session():
    """테스트 DB 세션"""
    db = next(get_db())
    yield db
    db.rollback()
    db.close()


@pytest.fixture
def indexer(db_session):
    """문서 인덱서"""
    return DocumentIndexer(db_session=db_session)


def test_index_pdf_document(indexer):
    """TC01: PDF 문서 인덱싱"""
    pdf_path = "tests/fixtures/pdf/sample_valid.pdf"

    if not Path(pdf_path).exists():
        pytest.skip("PDF 파일 없음")

    result = indexer.index_document(pdf_path)

    assert result.success is True
    assert result.document_id is not None
    assert result.total_chunks > 0
    assert result.indexed_chunks == result.total_chunks


def test_index_docx_document(indexer):
    """TC02: DOCX 문서 인덱싱"""
    docx_path = "tests/fixtures/docx/sample_valid.docx"

    if not Path(docx_path).exists():
        pytest.skip("DOCX 파일 없음")

    result = indexer.index_document(docx_path)

    assert result.success is True
    assert result.indexed_chunks > 0


def test_postgresql_metadata_saved(indexer, db_session):
    """TC03: PostgreSQL 메타데이터 저장 확인"""
    pdf_path = "tests/fixtures/pdf/sample_valid.pdf"

    if not Path(pdf_path).exists():
        pytest.skip("PDF 파일 없음")

    result = indexer.index_document(pdf_path)

    # DB에서 확인
    document = db_session.query(Document).filter(
        Document.id == result.document_id
    ).first()

    assert document is not None
    assert document.title is not None
    assert document.file_path == pdf_path
    assert document.chunk_count == result.indexed_chunks


def test_milvus_vectors_saved(indexer):
    """TC04: Milvus 벡터 저장 확인"""
    pdf_path = "tests/fixtures/pdf/sample_valid.pdf"

    if not Path(pdf_path).exists():
        pytest.skip("PDF 파일 없음")

    result = indexer.index_document(pdf_path)

    # Milvus에서 확인
    collection = indexer.collection
    collection.load()

    expr = f"document_id == {result.document_id}"
    search_result = collection.query(expr=expr, output_fields=["document_id"])

    assert len(search_result) == result.indexed_chunks


def test_embedding_dimension(indexer):
    """TC05: 임베딩 차원 검증 (768)"""
    pdf_path = "tests/fixtures/pdf/sample_valid.pdf"

    if not Path(pdf_path).exists():
        pytest.skip("PDF 파일 없음")

    result = indexer.index_document(pdf_path)

    # Milvus에서 벡터 확인
    collection = indexer.collection
    collection.load()

    expr = f"document_id == {result.document_id}"
    vectors = collection.query(
        expr=expr,
        output_fields=["embedding"],
        limit=1
    )

    if vectors:
        embedding = vectors[0]["embedding"]
        assert len(embedding) == 768


def test_batch_indexing(indexer):
    """TC06: 배치 인덱싱"""
    file_paths = [
        "tests/fixtures/pdf/sample_valid.pdf",
        "tests/fixtures/docx/sample_valid.docx",
        "tests/fixtures/txt/sample_valid.txt",
    ]

    # 존재하는 파일만 필터
    existing_files = [f for f in file_paths if Path(f).exists()]

    if not existing_files:
        pytest.skip("테스트 파일 없음")

    results = indexer.index_batch(existing_files)

    assert len(results) == len(existing_files)
    assert all(r.success for r in results)


def test_delete_document(indexer, db_session):
    """TC07: 문서 삭제"""
    pdf_path = "tests/fixtures/pdf/sample_valid.pdf"

    if not Path(pdf_path).exists():
        pytest.skip("PDF 파일 없음")

    # 인덱싱
    result = indexer.index_document(pdf_path)
    document_id = result.document_id

    # 삭제
    success = indexer.delete_document(document_id)

    assert success is True

    # PostgreSQL 확인
    document = db_session.query(Document).filter(
        Document.id == document_id
    ).first()
    assert document is None

    # Milvus 확인
    collection = indexer.collection
    expr = f"document_id == {document_id}"
    search_result = collection.query(expr=expr)
    assert len(search_result) == 0
```

---

### 4.5 Step 5: 통합 테스트 스크립트 작성 (30min)

#### 작업 내용
`scripts/test_full_pipeline.py`:

```python
#!/usr/bin/env python3
"""
전체 파이프라인 통합 테스트 스크립트

Usage:
    python scripts/test_full_pipeline.py
"""

import sys
from pathlib import Path
from app.services.document_indexer import DocumentIndexer
from app.db.session import get_db


def test_pipeline():
    """전체 파이프라인 테스트"""
    print("📄 전체 파이프라인 테스트 시작\n")

    # 테스트 문서 목록
    test_docs = [
        "tests/fixtures/pdf/sample_valid.pdf",
        "tests/fixtures/docx/sample_valid.docx",
        "tests/fixtures/txt/sample_valid.txt",
        "tests/fixtures/markdown/sample_valid.md",
    ]

    # 존재하는 파일만 필터
    existing_docs = [doc for doc in test_docs if Path(doc).exists()]

    if not existing_docs:
        print("❌ 테스트 문서가 없습니다.")
        return False

    print(f"📋 테스트 문서: {len(existing_docs)}개\n")

    # DB 세션 생성
    db = next(get_db())

    try:
        # 인덱서 생성
        indexer = DocumentIndexer(db_session=db)

        # 배치 인덱싱
        results = indexer.index_batch(existing_docs)

        # 결과 출력
        print("\n" + "=" * 60)
        print("📊 인덱싱 결과:")
        print("=" * 60)

        for result in results:
            status = "✅ 성공" if result.success else "❌ 실패"
            print(f"\n{status}: {Path(result.file_path).name}")
            print(f"  - 문서 ID: {result.document_id}")
            print(f"  - 총 청크: {result.total_chunks}")
            print(f"  - 인덱싱된 청크: {result.indexed_chunks}")
            print(f"  - 처리 시간: {result.processing_time_ms}ms")

            if not result.success:
                print(f"  - 에러: {result.error_message}")

        # 통계
        success_count = sum(1 for r in results if r.success)
        total_chunks = sum(r.indexed_chunks for r in results)

        print("\n" + "=" * 60)
        print(f"✅ 성공: {success_count}/{len(results)}")
        print(f"📦 총 청크: {total_chunks}개")
        print("=" * 60)

        return success_count == len(results)

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = test_pipeline()
    sys.exit(0 if success else 1)
```

---

### 4.6 Step 6: Attu UI 검증 및 문서화 (30min)

#### 작업 내용

1. **Attu UI에서 벡터 확인**
   ```bash
   # Attu UI 접속
   open http://localhost:8080

   # Collection 선택: documents
   # Entities 확인:
   # - document_id
   # - chunk_index
   # - content
   # - embedding (768차원)
   # - page_number
   # - metadata
   ```

2. **PostgreSQL 데이터 확인**
   ```bash
   psql -h localhost -U postgres -d rag_platform

   # 문서 목록 확인
   SELECT id, title, file_type, chunk_count, indexed_at FROM documents;

   # 특정 문서 상세
   SELECT * FROM documents WHERE id = 1;
   ```

3. **문서화** (`docs/api/document_indexer_usage.md`):

```markdown
# Document Indexer Usage Guide

## 전체 파이프라인
파싱 → 청킹 → 임베딩 → 저장

## 사용 예제

### 단일 문서 인덱싱
\`\`\`python
from app.services.document_indexer import DocumentIndexer
from app.db.session import get_db

db = next(get_db())
indexer = DocumentIndexer(db_session=db)

result = indexer.index_document("document.pdf")

if result.success:
    print(f"성공! 문서 ID: {result.document_id}")
    print(f"청크 수: {result.indexed_chunks}")
else:
    print(f"실패: {result.error_message}")
\`\`\`

### 배치 인덱싱
\`\`\`python
file_paths = ["doc1.pdf", "doc2.docx", "doc3.txt"]
results = indexer.index_batch(file_paths)

success_count = sum(1 for r in results if r.success)
print(f"성공: {success_count}/{len(results)}")
\`\`\`

### 문서 삭제
\`\`\`python
success = indexer.delete_document(document_id=1)
\`\`\`
```

---

## 5. 검증 및 수동 테스트

### 5.1 자동화 테스트 검증
```bash
# 모든 테스트 실행
pytest tests/test_embedding_service.py -v
pytest tests/test_document_indexer.py -v

# 통합 테스트
python scripts/test_full_pipeline.py
```

### 5.2 수동 검증 체크리스트
- [ ] 10개 테스트 문서 인덱싱 성공
- [ ] Attu UI에서 벡터 확인 (768차원)
- [ ] PostgreSQL에서 메타데이터 확인
- [ ] 임베딩 차원 768 검증
- [ ] 배치 처리 정상 동작
- [ ] 재시도 로직 동작 (네트워크 끊었다 연결)
- [ ] 롤백 메커니즘 검증 (중간에 에러 발생)

### 5.3 성능 검증
```bash
# 10개 문서 인덱싱 시간 측정
time python scripts/test_full_pipeline.py

# 목표: < 5분 (10개 문서)
```

---

## 6. 산출물 (Deliverables)

### 6.1 코드 파일
- [x] `app/services/embedding_service.py` (임베딩 서비스)
- [x] `app/services/document_indexer.py` (문서 인덱서)
- [x] `tests/test_embedding_service.py` (5개 테스트)
- [x] `tests/test_document_indexer.py` (7개 테스트)
- [x] `scripts/test_full_pipeline.py` (통합 테스트 스크립트)

### 6.2 문서
- [x] `docs/api/document_indexer_usage.md` (사용 가이드)

---

## 7. 리스크 및 대응 방안

### 7.1 기술 리스크

#### Risk 1: Ollama 임베딩 품질 부족
**증상**:
- 검색 정확도 낮음
- 관련 없는 문서 검색됨

**확률**: Medium (30%)

**대응**:
1. **즉시 대응**:
   - Task 1.8 완료 후 품질 평가 (10개 샘플 검색)
   - 검색 정확도 측정

2. **단기 대응** (Task 2.5a):
   - OpenAI embedding으로 전환 준비
   - 임베딩 서비스 추상화 (Provider 패턴)

---

#### Risk 2: Milvus 저장 실패 (롤백 미작동)
**증상**:
- PostgreSQL에는 저장, Milvus에는 없음
- 데이터 불일치

**확률**: Low (15%)

**대응**:
1. **즉시 대응**:
   - 트랜잭션 관리 강화
   - Milvus 저장 실패 시 PostgreSQL 롤백

2. **단기 대응**:
   - 정합성 검증 스크립트 작성
   - 주기적 검증 (Cron Job)

---

#### Risk 3: 대용량 문서 메모리 부족
**증상**:
- 10,000+ 청크 문서 처리 시 OOM
- 서버 다운

**확률**: Medium (20%)

**대응**:
1. **즉시 대응**:
   - 배치 크기 조정 (5 → 3)
   - 메모리 모니터링 추가

2. **단기 대응**:
   - 스트리밍 방식으로 변경
   - 청크별 순차 처리

---

#### Risk 4: Ollama 연결 실패 (재시도 고갈)
**증상**:
- 3회 재시도 후에도 실패
- 인덱싱 중단

**확률**: Low (10%)

**대응**:
1. **즉시 대응**:
   - 재시도 횟수 증가 (3 → 5)
   - Exponential backoff 적용

2. **단기 대응**:
   - Ollama Health check
   - 자동 재시작 스크립트

---

## 8. Next Steps (Task 1.8 완료 후)

### 8.1 즉시 수행
1. **Phase 1 완료 검증**
   - 전체 파이프라인 테스트 (파싱 → 청킹 → 임베딩 → 저장)
   - 10개 문서 인덱싱 성공 확인
   - Attu UI + PostgreSQL 데이터 확인

2. **코드 리뷰 요청**
   - Backend Lead에게 리뷰 요청
   - 보안, 성능, 안정성 검토

3. **Git 커밋**
   ```bash
   git add .
   git commit -m "feat: Implement document indexing pipeline (Task 1.8)

   - Add OllamaEmbeddingService with nomic-embed-text
   - Add DocumentIndexer (parse → chunk → embed → store)
   - Implement batch processing (5 documents parallel)
   - Add retry logic (3 attempts with exponential backoff)
   - Add rollback mechanism (PostgreSQL + Milvus)
   - Add comprehensive tests (embedding + indexer)
   - Add full pipeline integration test script
   - Verify 768-dimension embeddings in Milvus
   - Complete Phase 1: Document Processing Pipeline

   Closes #8"
   ```

### 8.2 Phase 1 완료 리뷰
**Success Criteria 확인**:
- [ ] 문서 인덱싱 성공 (10개 테스트 문서)
- [ ] Milvus에 벡터 저장 확인 (Attu UI)
- [ ] PostgreSQL에 메타데이터 저장 확인
- [ ] Ollama 모델 정상 동작 (llama3, nomic-embed-text)

### 8.3 Phase 2 준비
**Task 2.1: FastAPI 기본 구조 및 라우터 설정** 준비:
- [ ] FastAPI 프로젝트 구조 검토
- [ ] API 엔드포인트 설계
- [ ] 인증/인가 전략 검토

---

## 9. Appendix

### 9.1 참고 자료
- [Ollama Python Library](https://github.com/ollama/ollama-python)
- [nomic-embed-text Model Card](https://huggingface.co/nomic-ai/nomic-embed-text-v1)
- [Milvus Python SDK](https://milvus.io/docs/install-pymilvus.md)
- [tenacity Retry Library](https://tenacity.readthedocs.io/)

### 9.2 Milvus Collection 스키마 (참고)

```python
# Task 1.3에서 생성됨
schema = CollectionSchema(
    fields=[
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="document_id", dtype=DataType.INT64),
        FieldSchema(name="chunk_index", dtype=DataType.INT64),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        FieldSchema(name="page_number", dtype=DataType.INT64),
        FieldSchema(name="metadata", dtype=DataType.JSON),
    ],
    description="Documents collection"
)

# 인덱스: HNSW (M=16, efConstruction=256), 메트릭: COSINE
```

### 9.3 유용한 커맨드

```bash
# Ollama 모델 확인
docker exec -it ollama ollama list

# nomic-embed-text 테스트
docker exec -it ollama ollama run nomic-embed-text "test"

# Milvus 연결 테스트
python -c "from pymilvus import connections; connections.connect('default', host='localhost', port='19530'); print('OK')"

# Attu UI 접속
open http://localhost:8080

# PostgreSQL 접속
psql -h localhost -U postgres -d rag_platform

# 전체 파이프라인 테스트
python scripts/test_full_pipeline.py
```

### 9.4 트러블슈팅

**문제**: `ModuleNotFoundError: No module named 'ollama'`
**해결**:
```bash
source venv/bin/activate
pip install ollama==0.1.6
```

**문제**: Ollama 연결 실패
**해결**:
```bash
# Ollama 컨테이너 재시작
docker restart ollama

# 모델 다시 다운로드
docker exec -it ollama ollama pull nomic-embed-text
```

**문제**: Milvus 저장 실패 (차원 불일치)
**해결**:
```python
# 임베딩 차원 확인
embedding = embedding_service.embed_text("test")
print(f"Dimension: {len(embedding)}")  # 768이어야 함

# Collection 스키마 확인
collection.schema
```

**문제**: PostgreSQL 롤백 안 됨
**해결**:
```python
# 트랜잭션 명시적 관리
try:
    # ... 인덱싱 작업 ...
    db.commit()
except Exception:
    db.rollback()
    raise
```

---

## 10. Approval & Sign-off

### 10.1 체크리스트
Task 1.8 완료 조건:
- [ ] 10개 테스트 문서 인덱싱 성공
- [ ] Attu UI에서 벡터 확인 (768차원)
- [ ] PostgreSQL에 메타데이터 저장 확인
- [ ] 임베딩 차원 검증 (768차원)
- [ ] 배치 처리 정상 동작 (5개 병렬)
- [ ] 재시도 로직 동작 확인
- [ ] 롤백 메커니즘 검증
- [ ] 통합 테스트 스크립트 동작
- [ ] 성능: 10개 문서 < 5분
- [ ] 코드 커버리지 ≥ 85%
- [ ] 코드 리뷰 승인
- [ ] 문서화 완료

### 10.2 Phase 1 완료 승인
- [ ] **Backend Lead**: _______________
- [ ] **Tech Lead**: _______________
- [ ] **Infrastructure Team**: _______________

**Review Deadline**: Task 1.8 완료 후 48시간 이내

---

**END OF EXECUTION PLAN - PHASE 1 COMPLETE!** 🎉
