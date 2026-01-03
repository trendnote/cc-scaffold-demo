# Task 2.5b: LLM 안정성 강화 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.5b
- **Task명**: LLM 안정성 강화
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation (Task 2.5a 직후 진행)
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
Hallucination 방지, 타임아웃 처리, 재시도 로직을 추가하여 LLM 답변 생성의 안정성을 강화합니다.

### 1.2 핵심 요구사항
- **보안**: [HARD RULE] 검색된 문서만 사용, 출처 없는 답변 금지
- **안정성**: 30초 타임아웃, 3회 재시도 (exponential backoff)
- **품질**: Confidence threshold 0.5, Hallucination 0건
- **성공 기준**: 출처 정확도 100%, Hallucination 방지 테스트 100% 통과

### 1.3 성공 기준
- [ ] 관련 문서 없을 때 Fallback 메시지 반환
- [ ] Confidence < 0.5 시 Fallback 메시지 반환
- [ ] LLM 타임아웃 시 재시도 → Fallback
- [ ] 출처 없는 답변 거부
- [ ] Hallucination 방지 테스트 5개 케이스 통과

### 1.4 Why This Task Matters
**신뢰할 수 있는 RAG 시스템**:
- **Hallucination 방지**: 거짓 정보 생성 차단
- **사용자 신뢰**: 항상 출처가 있는 답변만 제공
- **시스템 안정성**: LLM 장애 시에도 서비스 유지

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Task 2.5a 완료 확인
ls -la backend/app/services/rag_service.py
ls -la backend/app/services/llm/ollama_provider.py

# Tenacity 설치 확인 (재시도 로직)
python -c "import tenacity; print(tenacity.__version__)"
```

### 2.2 의존성 확인
- [x] **Task 2.5a**: RAGService 기본 구현 완료
- [x] **Task 2.3**: VectorSearchService 완료
- [x] **requirements.txt**: tenacity (이미 Task 1.8에서 설치됨)

---

## 3. 안정성 강화 전략

### 3.1 Hallucination 방지 메커니즘

```
검색 결과 확인
    ↓
검색 결과 없음? → Fallback: "관련 문서를 찾을 수 없습니다"
    ↓
관련도 점수 확인
    ↓
평균 관련도 < 0.5? → Fallback: "답변을 찾을 수 없습니다"
    ↓
LLM 답변 생성
    ↓
출처 검증 (답변에 출처 포함?)
    ↓
출처 없음? → 재생성 또는 Fallback
    ↓
최종 답변 반환
```

### 3.2 타임아웃 및 재시도

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
async def generate_with_timeout(prompt: str) -> str:
    """30초 타임아웃 + 3회 재시도"""
    async with timeout(30):
        return await llm_provider.generate(prompt)
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: Hallucination 방지 로직 (90분)

#### 작업 내용
**`backend/app/services/rag_service.py` 강화**:

```python
from typing import List, Optional
import re


class RAGService:
    # ... 기존 코드 ...

    CONFIDENCE_THRESHOLD = 0.5  # 최소 신뢰도
    FALLBACK_NO_DOCUMENTS = "죄송합니다. 관련 문서를 찾을 수 없습니다."
    FALLBACK_LOW_CONFIDENCE = "답변을 찾을 수 없습니다. 아래 검색 결과를 참고하세요."
    FALLBACK_NO_SOURCE = "답변 생성에 실패했습니다. 검색 결과를 확인해 주세요."

    def generate_answer(
        self,
        query: str,
        search_results: List[SearchResult]
    ) -> str:
        """
        검색 결과 기반 답변 생성 (Hallucination 방지)

        Args:
            query: 사용자 질문
            search_results: 벡터 검색 결과

        Returns:
            str: 생성된 답변 (Fallback 포함)
        """
        # [STEP 1] 검색 결과 없음 → Fallback
        if not search_results:
            logger.warning("검색 결과 없음, Fallback 반환")
            return self.FALLBACK_NO_DOCUMENTS

        # [STEP 2] 관련도 점수 확인
        avg_relevance = sum(r.relevance_score for r in search_results) / len(search_results)

        if avg_relevance < self.CONFIDENCE_THRESHOLD:
            logger.warning(
                f"낮은 관련도 (avg={avg_relevance:.3f}), Fallback 반환"
            )
            return self.FALLBACK_LOW_CONFIDENCE

        # [STEP 3] Context 구성
        context = self._build_context(search_results)

        # [STEP 4] 프롬프트 구성
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            query=query
        )

        # [STEP 5] LLM 답변 생성 (타임아웃 + 재시도)
        try:
            answer = self._generate_with_retry(prompt)

            # [STEP 6] 출처 검증
            if not self._has_source_citation(answer):
                logger.error(
                    "출처 미포함 답변 거부: answer='{answer[:100]}...'"
                )
                return self.FALLBACK_NO_SOURCE

            logger.info("RAG 답변 생성 성공 (출처 검증 완료)")
            return answer

        except Exception as e:
            logger.error(f"RAG 답변 생성 실패: {e}")
            return self.FALLBACK_NO_SOURCE

    def _has_source_citation(self, answer: str) -> bool:
        """
        답변에 출처가 포함되어 있는지 확인

        Args:
            answer: 생성된 답변

        Returns:
            bool: 출처 포함 여부
        """
        # 출처 패턴: "문서", "출처", "규정", "에 따르면" 등
        citation_patterns = [
            r"문서",
            r"출처",
            r"규정",
            r"에 따르면",
            r"따라서",
            r"\[문서 \d+\]"  # [문서 1], [문서 2] 등
        ]

        for pattern in citation_patterns:
            if re.search(pattern, answer):
                return True

        logger.warning(f"출처 미포함: answer='{answer[:100]}...'")
        return False
```

---

### 4.2 Step 2: 타임아웃 및 재시도 로직 (60분)

#### 작업 내용
**`backend/app/services/rag_service.py` 재시도 로직 추가**:

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
import asyncio


class RAGService:
    # ... 기존 코드 ...

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry_if_exception_type=TimeoutError,
        reraise=True
    )
    def _generate_with_retry(self, prompt: str) -> str:
        """
        재시도 로직이 포함된 LLM 답변 생성

        Args:
            prompt: 프롬프트

        Returns:
            str: 생성된 답변

        Raises:
            TimeoutError: 30초 타임아웃
            ValueError: LLM 생성 실패
        """
        logger.info("LLM 답변 생성 시작 (타임아웃: 30초)")

        try:
            # 30초 타임아웃 설정
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("LLM 답변 생성 타임아웃 (30초)")

            # Timeout 설정
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)

            try:
                answer = self.llm_provider.generate(prompt)
                signal.alarm(0)  # 타임아웃 해제
                return answer

            except TimeoutError:
                signal.alarm(0)
                logger.warning("LLM 타임아웃 발생, 재시도...")
                raise

        except Exception as e:
            logger.error(f"LLM 답변 생성 실패: {e}")
            raise ValueError(f"LLM 답변 생성 실패: {e}")
```

---

### 4.3 Step 3: Fallback 전략 (60분)

#### 작업 내용
**Fallback 응답 형식 표준화**:

```python
class RAGService:
    # ... 기존 코드 ...

    def generate_answer_with_fallback(
        self,
        query: str,
        search_results: List[SearchResult]
    ) -> dict:
        """
        Fallback 정보를 포함한 답변 생성

        Returns:
            dict: {
                "answer": str,
                "is_fallback": bool,
                "fallback_reason": Optional[str],
                "search_results": List[SearchResult]
            }
        """
        # 답변 생성 시도
        answer = self.generate_answer(query, search_results)

        # Fallback 여부 확인
        is_fallback = answer in [
            self.FALLBACK_NO_DOCUMENTS,
            self.FALLBACK_LOW_CONFIDENCE,
            self.FALLBACK_NO_SOURCE
        ]

        fallback_reason = None
        if is_fallback:
            if answer == self.FALLBACK_NO_DOCUMENTS:
                fallback_reason = "no_documents"
            elif answer == self.FALLBACK_LOW_CONFIDENCE:
                fallback_reason = "low_confidence"
            elif answer == self.FALLBACK_NO_SOURCE:
                fallback_reason = "no_source_citation"

        return {
            "answer": answer,
            "is_fallback": is_fallback,
            "fallback_reason": fallback_reason,
            "search_results": search_results if is_fallback else []
        }
```

---

### 4.4 Step 4: 통합 테스트 (60분)

#### 작업 내용
**`backend/tests/test_hallucination_prevention.py` 작성**:

```python
import pytest
from app.services.rag_service import RAGService
from app.services.vector_search import SearchResult


def test_no_search_results_fallback():
    """TC01: 검색 결과 없을 때 Fallback"""
    rag_service = RAGService()

    answer = rag_service.generate_answer(
        query="존재하지 않는 문서 질문",
        search_results=[]
    )

    assert "관련 문서를 찾을 수 없습니다" in answer


def test_low_confidence_fallback():
    """TC02: 낮은 관련도 점수 → Fallback"""
    rag_service = RAGService()

    # 관련도 0.3인 결과 (threshold 0.5 미만)
    low_confidence_results = [
        SearchResult(
            document_id="doc_001",
            chunk_index=0,
            content="관련 없는 내용",
            page_number=1,
            relevance_score=0.3,
            metadata={}
        )
    ]

    answer = rag_service.generate_answer(
        query="테스트 질문",
        search_results=low_confidence_results
    )

    assert "답변을 찾을 수 없습니다" in answer


def test_answer_with_source_citation():
    """TC03: 출처가 포함된 답변 검증"""
    rag_service = RAGService()

    # Mock: 출처 포함 답변
    answer = "휴가 규정 문서에 따르면 연차는 입사일 기준 1년 후부터 사용 가능합니다."

    has_source = rag_service._has_source_citation(answer)

    assert has_source is True


def test_answer_without_source_rejected():
    """TC04: 출처 없는 답변 거부"""
    rag_service = RAGService()

    # Mock: 출처 없는 답변
    answer = "연차는 1년 후부터 사용 가능합니다."

    has_source = rag_service._has_source_citation(answer)

    assert has_source is False


def test_timeout_retry_mechanism():
    """TC05: 타임아웃 재시도 메커니즘"""
    # TODO: Mock LLM Provider로 타임아웃 시뮬레이션
    pass
```

---

## 5. 테스트 계획

### 5.1 Hallucination 방지 테스트 (5개)

```bash
pytest backend/tests/test_hallucination_prevention.py -v
# 예상: 5 passed
```

### 5.2 통합 테스트

```bash
pytest backend/tests/integration/test_rag_stability.py -v
# 예상: 5 passed (End-to-End 안정성 검증)
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] 검색 결과 없을 때 Fallback 반환
- [ ] Confidence < 0.5 시 Fallback 반환
- [ ] LLM 타임아웃 시 재시도 (3회)
- [ ] 출처 없는 답변 거부
- [ ] Hallucination 방지 테스트 5개 통과
- [ ] 타임아웃 30초 이내 응답

### 6.2 품질 기준

- [ ] 출처 정확도 100% (모든 답변에 출처 포함)
- [ ] Hallucination 0건

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/tests/test_hallucination_prevention.py` - Hallucination 방지 테스트 (5개)
2. `backend/tests/integration/test_rag_stability.py` - 통합 테스트

### 7.2 수정될 파일

1. `backend/app/services/rag_service.py` - 안정성 강화 로직 추가

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 2.5a Plan: `docs/task-plans/task-2.5a-plan.md`
- Hallucination Prevention: https://arxiv.org/abs/2305.14251

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
