"""
RAG (Retrieval-Augmented Generation) 서비스

Task 2.5a: LLM 기본 답변 생성
Task 2.5b: LLM 안정성 강화 (Hallucination 방지, 타임아웃, 재시도)
"""

import os
import re
import signal
from typing import List, Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.vector_search import SearchResult
import logging

logger = logging.getLogger(__name__)


# RAG 프롬프트 템플릿 로드
def load_rag_prompt_template() -> str:
    """RAG 프롬프트 템플릿 로드"""
    prompt_file = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..",
        "prompts",
        "rag_prompt.txt"
    )

    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            template = f.read()
        logger.debug(f"프롬프트 템플릿 로드 성공: {prompt_file}")
        return template
    except FileNotFoundError:
        logger.warning(f"프롬프트 템플릿 파일 없음: {prompt_file}, 기본 템플릿 사용")
        # 기본 템플릿
        return """다음 문서를 참고하여 질문에 답변하세요.

[문서]
{context}

[질문]
{query}

[규칙]
1. 반드시 위 문서의 내용만 사용하여 답변하세요.
2. 문서에 없는 내용은 답하지 마세요.
3. 답변에 반드시 출처를 명시하세요 (예: "휴가 규정 문서에 따르면...").
4. 한국어로 자연스럽게 답변하세요.
5. 답변은 3-5문장으로 간결하게 작성하세요.

[답변]
"""


# 프롬프트 템플릿 로드
RAG_PROMPT_TEMPLATE = load_rag_prompt_template()


class RAGService:
    """RAG (Retrieval-Augmented Generation) 서비스"""

    # Task 2.5b: Hallucination 방지 상수
    CONFIDENCE_THRESHOLD = 0.5  # 최소 신뢰도
    FALLBACK_NO_DOCUMENTS = "죄송합니다. 관련 문서를 찾을 수 없습니다."
    FALLBACK_LOW_CONFIDENCE = "답변을 찾을 수 없습니다. 아래 검색 결과를 참고하세요."
    FALLBACK_NO_SOURCE = "답변 생성에 실패했습니다. 검색 결과를 확인해 주세요."

    def __init__(self, provider_type: str = "ollama"):
        """
        Args:
            provider_type: "ollama" 또는 "openai"

        Raises:
            ValueError: 알 수 없는 provider_type일 때
        """
        self.provider_type = provider_type

        # LLM Provider 초기화
        if provider_type == "ollama":
            self.llm_provider = OllamaProvider()
        elif provider_type == "openai":
            self.llm_provider = OpenAIProvider()
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")

        logger.info(f"RAGService 초기화: provider={provider_type}")

    def generate_answer(
        self,
        query: str,
        search_results: List[SearchResult]
    ) -> str:
        """
        검색 결과 기반 답변 생성 (Task 2.5b: Hallucination 방지 강화)

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

        # [STEP 2] 관련도 점수 확인 (Task 2.5b)
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

        logger.info(
            f"RAG 답변 생성 시작: query='{query[:50]}...', "
            f"context_length={len(context)}, avg_relevance={avg_relevance:.3f}"
        )

        # [STEP 5] LLM 답변 생성 (타임아웃 + 재시도)
        try:
            answer = self._generate_with_retry(prompt)

            # [STEP 6] 출처 검증 (Task 2.5b)
            if not self._has_source_citation(answer):
                logger.error(
                    f"출처 미포함 답변 거부: answer='{answer[:100]}...'"
                )
                return self.FALLBACK_NO_SOURCE

            logger.info("RAG 답변 생성 성공 (출처 검증 완료)")
            return answer

        except Exception as e:
            logger.error(f"RAG 답변 생성 실패: {e}")
            return self.FALLBACK_NO_SOURCE

    def _build_context(self, search_results: List[SearchResult]) -> str:
        """
        검색 결과를 LLM 컨텍스트로 변환

        Args:
            search_results: 검색 결과 리스트

        Returns:
            str: 컨텍스트 문자열
        """
        context_parts = []

        for idx, result in enumerate(search_results, 1):
            doc_title = result.metadata.get("document_title", "Unknown")
            doc_source = result.metadata.get("document_source", "Unknown")
            page_num = result.page_number or "N/A"

            context_part = (
                f"[문서 {idx}] {doc_title}\n"
                f"출처: {doc_source} (페이지 {page_num})\n"
                f"내용: {result.content}\n"
                f"관련도: {result.relevance_score:.2f}\n"
            )

            context_parts.append(context_part)

        return "\n---\n".join(context_parts)

    def _has_source_citation(self, answer: str) -> bool:
        """
        답변에 출처가 포함되어 있는지 확인 (Task 2.5b)

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

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TimeoutError),
        reraise=True
    )
    def _generate_with_retry(self, prompt: str) -> str:
        """
        재시도 로직이 포함된 LLM 답변 생성 (Task 2.5b)

        Args:
            prompt: 프롬프트

        Returns:
            str: 생성된 답변

        Raises:
            TimeoutError: 60초 타임아웃
            ValueError: LLM 생성 실패
        """
        logger.info("LLM 답변 생성 시작 (타임아웃: 60초)")

        def timeout_handler(signum, frame):
            raise TimeoutError("LLM 답변 생성 타임아웃 (60초)")

        try:
            # Timeout 설정 (60초)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)

            try:
                answer = self.llm_provider.generate(prompt)
                signal.alarm(0)  # 타임아웃 해제
                return answer

            except TimeoutError:
                signal.alarm(0)
                logger.warning("LLM 타임아웃 발생, 재시도...")
                raise

        except Exception as e:
            signal.alarm(0)  # 타임아웃 해제 (안전)
            logger.error(f"LLM 답변 생성 실패: {e}")
            raise ValueError(f"LLM 답변 생성 실패: {e}")

    def generate_answer_with_fallback(
        self,
        query: str,
        search_results: List[SearchResult]
    ) -> Dict[str, Any]:
        """
        Fallback 정보를 포함한 답변 생성 (Task 2.5b)

        Args:
            query: 사용자 질문
            search_results: 벡터 검색 결과

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
