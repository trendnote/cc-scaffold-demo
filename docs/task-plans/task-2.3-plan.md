# Task 2.3: 벡터 검색 기능 구현 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.3
- **Task명**: 벡터 검색 기능 구현
- **예상 시간**: 6시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
Milvus 벡터 데이터베이스에서 유사도 기반 검색을 구현하여 사용자 질문에 관련된 문서 청크를 찾습니다.

### 1.2 핵심 요구사항
- **기능**: 쿼리 임베딩 생성, Milvus COSINE 유사도 검색, 상위 5개 결과 반환
- **성능**: [HARD RULE] P95 < 1초 (95%의 검색이 1초 이내 완료)
- **품질**: 관련도 점수 0.7 이상 결과만 반환
- **안정성**: 검색 실패 시 재시도 로직 (3회)

### 1.3 성공 기준
- [ ] 쿼리 임베딩 생성 성공 (768차원)
- [ ] Milvus 검색 성공 (상위 5개 결과)
- [ ] P95 검색 시간 < 1초
- [ ] 관련도 점수 정규화 (0-1)
- [ ] 단위 테스트 10개 케이스 통과
- [ ] 통합 테스트 10개 시나리오 통과

### 1.4 Why This Task Matters
**RAG 시스템의 핵심 엔진**:
- **검색 품질**: 정확한 문서 검색이 답변 품질 결정
- **사용자 경험**: 빠른 검색 속도로 대기 시간 최소화
- **확장성**: 수십만 문서에서도 1초 이내 검색

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 1.8 완료 확인 (임베딩 서비스)
ls -la backend/app/services/embedding_service.py

# Task 1.3 완료 확인 (Milvus Collection)
python -c "from pymilvus import utility; print(utility.list_collections())"

# Ollama nomic-embed-text 모델 확인
ollama list | grep nomic-embed-text
```

### 2.2 의존성 확인
- [x] **Task 1.3**: Milvus Collection 생성 완료 (documents)
- [x] **Task 1.4**: Ollama nomic-embed-text 모델 다운로드 완료
- [x] **Task 1.8**: OllamaEmbeddingService 구현 완료
- [x] **Task 2.1**: FastAPI 기본 구조 완료
- [x] **Task 2.2**: 검색어 검증 완료

---

## 3. 기술 스택 및 설계

### 3.1 Milvus 검색 파라미터

**선택한 설정**:
```python
search_params = {
    "metric_type": "COSINE",  # 코사인 유사도 (각도 기반)
    "params": {"ef": 64}      # HNSW 검색 정확도 파라미터
}
```

**선택 이유**:
- **COSINE**: 텍스트 임베딩에 가장 적합 (방향만 고려)
- **ef=64**: 정확도와 속도 균형 (기본값 10보다 높음)

### 3.2 검색 플로우

```
사용자 쿼리 입력
    ↓
1. 검색어 임베딩 생성 (OllamaEmbeddingService)
    ↓
2. Milvus 벡터 검색 (COSINE, top_k=5)
    ↓
3. 관련도 점수 필터링 (≥ 0.7)
    ↓
4. 결과 정규화 및 정렬
    ↓
검색 결과 반환 (List[DocumentChunk])
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: 쿼리 임베딩 서비스 확장 (90분)

#### 작업 내용
기존 `OllamaEmbeddingService`를 그대로 사용하되, 검색 전용 메서드 추가

**`backend/app/services/embedding_service.py` 확장**:

```python
class OllamaEmbeddingService:
    # ... 기존 코드 ...

    def embed_query(self, query: str) -> List[float]:
        """
        검색 쿼리 임베딩 생성

        Args:
            query: 검색어 (이미 검증 완료)

        Returns:
            List[float]: 768차원 임베딩 벡터

        Raises:
            EmbeddingServiceError: 임베딩 생성 실패
        """
        logger.info(f"검색 쿼리 임베딩 생성: '{query[:50]}...'")

        try:
            embedding = self.embed_text(query)

            logger.info(
                f"임베딩 생성 성공: dimension={len(embedding)}, "
                f"query_length={len(query)}"
            )

            return embedding

        except Exception as e:
            logger.error(f"검색 쿼리 임베딩 실패: {e}")
            raise EmbeddingServiceError(f"검색 쿼리 임베딩 실패: {e}")
```

#### 검증
```python
# 임베딩 생성 테스트
embedding_service = OllamaEmbeddingService()
query_embedding = embedding_service.embed_query("연차 사용 방법")
assert len(query_embedding) == 768
```

---

### 4.2 Step 2: Milvus 벡터 검색 로직 (120분)

#### 작업 내용
`backend/app/services/vector_search.py` 작성:

```python
from typing import List, Optional
from dataclasses import dataclass
from pymilvus import Collection
import logging

from app.db.milvus_client import get_milvus_collection
from app.services.embedding_service import OllamaEmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """벡터 검색 결과"""
    document_id: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    relevance_score: float  # 0-1 정규화된 점수
    metadata: dict


class VectorSearchService:
    """Milvus 벡터 검색 서비스"""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_service: Optional[OllamaEmbeddingService] = None
    ):
        self.collection_name = collection_name
        self.embedding_service = embedding_service or OllamaEmbeddingService()
        self.collection: Optional[Collection] = None

        # 검색 파라미터
        self.search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64}
        }
        self.relevance_threshold = 0.7  # 최소 관련도 점수

        logger.info(
            f"VectorSearchService 초기화: collection={collection_name}, "
            f"threshold={self.relevance_threshold}"
        )

    def _ensure_collection(self):
        """Collection 로드 (lazy loading)"""
        if self.collection is None:
            self.collection = get_milvus_collection(self.collection_name)
            logger.info(f"Milvus Collection '{self.collection_name}' 로드 완료")

    def search(
        self,
        query: str,
        top_k: int = 5,
        filter_expr: Optional[str] = None
    ) -> List[SearchResult]:
        """
        벡터 유사도 검색 실행

        Args:
            query: 검색어
            top_k: 반환할 최대 결과 수
            filter_expr: Milvus 필터 표현식 (선택적, Task 2.4에서 사용)

        Returns:
            List[SearchResult]: 검색 결과 (관련도 내림차순 정렬)

        Raises:
            ValueError: Collection이 없거나 검색 실패 시
        """
        self._ensure_collection()

        # Step 1: 쿼리 임베딩 생성
        logger.info(f"검색 시작: query='{query[:50]}...', top_k={top_k}")
        query_embedding = self.embedding_service.embed_query(query)

        # Step 2: Milvus 검색 실행
        try:
            search_results = self.collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=self.search_params,
                limit=top_k,
                expr=filter_expr,
                output_fields=[
                    "document_id",
                    "chunk_index",
                    "content",
                    "page_number",
                    "metadata"
                ]
            )

            # Step 3: 결과 파싱 및 필터링
            results = self._parse_results(search_results[0])

            logger.info(
                f"검색 완료: found={len(results)}, "
                f"avg_score={sum(r.relevance_score for r in results) / len(results) if results else 0:.3f}"
            )

            return results

        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            raise ValueError(f"벡터 검색 실패: {e}")

    def _parse_results(self, raw_results) -> List[SearchResult]:
        """
        Milvus 검색 결과 파싱 및 필터링

        Args:
            raw_results: Milvus SearchResult 객체

        Returns:
            List[SearchResult]: 파싱된 검색 결과
        """
        results = []

        for hit in raw_results:
            # COSINE 유사도: -1 ~ 1 → 0 ~ 1로 정규화
            normalized_score = (hit.score + 1) / 2

            # 관련도 점수 필터링
            if normalized_score < self.relevance_threshold:
                logger.debug(
                    f"낮은 관련도로 제외: score={normalized_score:.3f}, "
                    f"content='{hit.entity.get('content', '')[:50]}...'"
                )
                continue

            result = SearchResult(
                document_id=hit.entity.get("document_id"),
                chunk_index=hit.entity.get("chunk_index"),
                content=hit.entity.get("content"),
                page_number=hit.entity.get("page_number"),
                relevance_score=normalized_score,
                metadata=hit.entity.get("metadata", {})
            )

            results.append(result)

        # 관련도 내림차순 정렬 (이미 정렬되어 있지만 명시적으로)
        results.sort(key=lambda r: r.relevance_score, reverse=True)

        return results
```

---

### 4.3 Step 3: 결과 후처리 및 통합 (60분)

#### 작업 내용
검색 결과를 API 응답 형식으로 변환

**`backend/app/services/search_service.py` 작성**:

```python
from typing import List
from app.schemas.search import DocumentSource
from app.services.vector_search import VectorSearchService, SearchResult
import logging

logger = logging.getLogger(__name__)


class SearchService:
    """통합 검색 서비스 (Task 2.3-2.6에서 점진적 완성)"""

    def __init__(self):
        self.vector_search = VectorSearchService()

    def search_documents(
        self,
        query: str,
        limit: int = 5,
        user_id: Optional[str] = None
    ) -> List[DocumentSource]:
        """
        문서 검색 (Task 2.3 버전: 벡터 검색만)

        Args:
            query: 검색어
            limit: 최대 결과 수
            user_id: 사용자 ID (Task 2.4에서 사용)

        Returns:
            List[DocumentSource]: 검색된 문서 출처 리스트
        """
        # Step 1: 벡터 검색
        search_results = self.vector_search.search(query, top_k=limit)

        # Step 2: DocumentSource 스키마로 변환
        sources = [
            DocumentSource(
                document_id=result.document_id,
                document_title=result.metadata.get("document_title", "Unknown"),
                document_source=result.metadata.get("document_source", "Unknown"),
                chunk_content=result.content,
                page_number=result.page_number,
                relevance_score=result.relevance_score
            )
            for result in search_results
        ]

        logger.info(f"검색 완료: query='{query}', results={len(sources)}")

        return sources
```

---

### 4.4 Step 4: 성능 테스트 및 최적화 (60분)

#### 성능 측정 스크립트

**`backend/tests/performance/test_search_performance.py`**:

```python
import time
import statistics
from app.services.vector_search import VectorSearchService

def test_search_performance():
    """100회 검색 성능 측정"""
    search_service = VectorSearchService()

    queries = [
        "연차 사용 방법",
        "급여 지급일",
        "휴가 신청 절차",
        "회의실 예약",
        "복리후생 제도"
    ] * 20  # 100개 쿼리

    response_times = []

    for query in queries:
        start_time = time.time()
        results = search_service.search(query, top_k=5)
        elapsed_ms = (time.time() - start_time) * 1000
        response_times.append(elapsed_ms)

    # 통계 계산
    p50 = statistics.median(response_times)
    p95 = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
    p99 = statistics.quantiles(response_times, n=100)[98]  # 99th percentile

    print(f"검색 성능 측정 (100회):")
    print(f"  P50: {p50:.2f}ms")
    print(f"  P95: {p95:.2f}ms")
    print(f"  P99: {p99:.2f}ms")

    # [HARD RULE] P95 < 1000ms 검증
    assert p95 < 1000, f"P95 성능 목표 미달: {p95:.2f}ms"
```

---

## 5. 테스트 계획

### 5.1 단위 테스트 (10개 케이스)

**`backend/tests/test_vector_search.py`**:

```python
import pytest
from app.services.vector_search import VectorSearchService

def test_vector_search_initialization():
    """TC01: VectorSearchService 초기화"""
    service = VectorSearchService()
    assert service.collection_name == "documents"
    assert service.relevance_threshold == 0.7

def test_search_returns_results():
    """TC02: 검색 결과 반환"""
    service = VectorSearchService()
    results = service.search("연차 사용 방법", top_k=5)

    assert isinstance(results, list)
    assert len(results) <= 5

def test_search_result_structure():
    """TC03: 검색 결과 구조 검증"""
    service = VectorSearchService()
    results = service.search("급여", top_k=5)

    if results:
        result = results[0]
        assert hasattr(result, 'document_id')
        assert hasattr(result, 'content')
        assert hasattr(result, 'relevance_score')
        assert 0 <= result.relevance_score <= 1

def test_relevance_score_threshold():
    """TC04: 관련도 점수 필터링 (≥ 0.7)"""
    service = VectorSearchService()
    results = service.search("test query", top_k=10)

    for result in results:
        assert result.relevance_score >= 0.7

def test_results_sorted_by_relevance():
    """TC05: 결과 관련도 내림차순 정렬"""
    service = VectorSearchService()
    results = service.search("연차", top_k=5)

    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i].relevance_score >= results[i + 1].relevance_score

# ... 5개 추가 테스트 케이스
```

### 5.2 통합 테스트 (10개 시나리오)

**`backend/tests/integration/test_search_integration.py`**:

```python
def test_end_to_end_search():
    """TC01: End-to-End 검색 플로우"""
    from app.services.search_service import SearchService

    service = SearchService()
    sources = service.search_documents("연차 사용 방법", limit=5)

    assert len(sources) > 0
    assert sources[0].relevance_score >= 0.7
    assert sources[0].document_id is not None
```

### 5.3 성능 테스트

```bash
pytest backend/tests/performance/test_search_performance.py -v -s
# 예상: P95 < 1000ms
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] 쿼리 임베딩 생성 성공 (768차원)
- [ ] Milvus 검색 성공 (상위 5개)
- [ ] 관련도 점수 정규화 (0-1)
- [ ] 관련도 점수 필터링 (≥ 0.7)
- [ ] 결과 관련도 내림차순 정렬
- [ ] 단위 테스트 10개 케이스 통과
- [ ] 통합 테스트 10개 시나리오 통과
- [ ] **P95 < 1초** (성능 목표)

### 6.2 품질 기준

- [ ] 코드 커버리지 ≥ 90%
- [ ] 에러 로깅 명확
- [ ] Collection 로드 lazy loading
- [ ] 재시도 로직 (선택적)

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/services/vector_search.py` (VectorSearchService)
2. `backend/app/services/search_service.py` (통합 서비스 - Task 2.3 버전)
3. `backend/tests/test_vector_search.py` (단위 테스트 10개)
4. `backend/tests/integration/test_search_integration.py` (통합 테스트)
5. `backend/tests/performance/test_search_performance.py` (성능 테스트)

### 7.2 수정될 파일

1. `backend/app/services/embedding_service.py` - `embed_query()` 메서드 추가
2. `backend/app/routers/search.py` - SearchService 통합 (Task 2.6에서 완성)

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 1.8 Completion: `logs/task-1.8-20260102-204612.md`
- Milvus Documentation: https://milvus.io/docs
- HNSW Algorithm: https://arxiv.org/abs/1603.09320

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
