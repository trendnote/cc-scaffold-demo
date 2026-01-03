# Task 2.5a: LLM 기본 답변 생성 - 실행 계획

---

## 📋 Meta

- **Task ID**: 2.5a
- **Task명**: LLM 기본 답변 생성
- **예상 시간**: 4시간
- **담당**: Backend
- **작성일**: 2026-01-03
- **상태**: Ready for Implementation
- **버전**: 1.0.0

---

## 1. Executive Summary

### 1.1 목표
LangChain RAG Chain을 사용하여 검색된 문서 기반 답변을 생성합니다. Ollama llama3를 우선 사용하되, 품질이 부족하면 OpenAI로 전환 가능한 구조로 설계합니다.

### 1.2 핵심 요구사항
- **기능**: LLM Provider 추상화 (Ollama/OpenAI 전환 가능)
- **품질**: 샘플 5개 질문으로 품질 평가 (Ollama vs OpenAI 결정)
- **출처**: [HARD RULE] 검색된 문서만 사용, 출처 명시 필수
- **성능**: LLM 호출 시간 < 25초

### 1.3 성공 기준
- [ ] Ollama llama3 모델 정상 동작
- [ ] OpenAI GPT-4 연동 구현 (환경 변수 전환만으로 변경 가능)
- [ ] RAG 프롬프트 템플릿 작성
- [ ] 샘플 5개 질문으로 품질 평가 완료
- [ ] 품질 평가 결과 문서화

### 1.4 Why This Task Matters
**RAG 시스템의 핵심 기능**:
- **답변 품질**: 검색 결과를 이해하기 쉬운 답변으로 변환
- **출처 신뢰성**: 검색된 문서만 사용하여 Hallucination 방지
- **유연성**: LLM Provider 교체 가능한 아키텍처

---

## 2. 선행 조건 검증

### 2.1 환경 검증
```bash
# Ollama llama3 모델 확인
ollama list | grep llama3

# LangChain 설치 확인
python -c "import langchain; print(langchain.__version__)"

# OpenAI API Key 확인 (선택적)
echo $OPENAI_API_KEY
```

### 2.2 의존성 확인
- [x] **Task 1.4**: Ollama llama3 모델 다운로드 완료
- [x] **Task 2.3**: VectorSearchService 구현 완료
- [ ] **requirements.txt**: langchain, langchain-community, openai

---

## 3. LLM Provider 아키텍처 설계

### 3.1 Provider 추상화

```python
from abc import ABC, abstractmethod
from typing import List


class BaseLLMProvider(ABC):
    """LLM Provider 추상 인터페이스"""

    @abstractmethod
    def generate(self, prompt: str, context: str) -> str:
        """
        프롬프트와 컨텍스트 기반 답변 생성

        Args:
            prompt: 사용자 질문
            context: 검색된 문서 내용

        Returns:
            str: 생성된 답변
        """
        pass


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM Provider (llama3)"""
    pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider (GPT-4)"""
    pass
```

### 3.2 Provider Factory 패턴

```python
class LLMProviderFactory:
    """LLM Provider 생성 팩토리"""

    @staticmethod
    def create(provider_type: str = "ollama") -> BaseLLMProvider:
        if provider_type == "ollama":
            return OllamaProvider()
        elif provider_type == "openai":
            return OpenAIProvider()
        else:
            raise ValueError(f"Unknown provider: {provider_type}")
```

---

## 4. 구현 단계별 상세 계획

### 4.1 Step 1: LLM Provider 추상화 (60분)

#### 작업 내용
**`backend/app/services/llm/base_provider.py` 작성**:

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """LLM 설정"""
    model_name: str = Field(..., description="모델명")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="온도")
    max_tokens: int = Field(default=500, ge=50, le=2000, description="최대 토큰")
    timeout: int = Field(default=30, description="타임아웃 (초)")


class BaseLLMProvider(ABC):
    """LLM Provider 추상 베이스 클래스"""

    def __init__(self, config: LLMConfig):
        self.config = config
        logger.info(
            f"{self.__class__.__name__} 초기화: "
            f"model={config.model_name}, "
            f"temperature={config.temperature}"
        )

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """
        프롬프트 기반 답변 생성

        Args:
            prompt: 전체 프롬프트 (질문 + 컨텍스트 포함)

        Returns:
            str: 생성된 답변

        Raises:
            LLMGenerationError: 답변 생성 실패 시
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Provider 상태 확인"""
        pass
```

---

### 4.2 Step 2: Ollama Provider 구현 (60분)

#### 작업 내용
**`backend/app/services/llm/ollama_provider.py` 작성**:

```python
import ollama
from app.services.llm.base_provider import BaseLLMProvider, LLMConfig
import logging

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM Provider (llama3)"""

    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                model_name="llama3",
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
        super().__init__(config)
        self.client = ollama.Client()

        # 모델 존재 확인
        if not self._verify_model_exists():
            raise ValueError(
                f"Ollama 모델 '{self.config.model_name}'이 없습니다. "
                f"다음 명령으로 다운로드하세요: ollama pull {self.config.model_name}"
            )

    def _verify_model_exists(self) -> bool:
        """Ollama 모델 존재 확인"""
        try:
            response = self.client.list()
            model_names = [model.model for model in response.models]
            search_names = [
                self.config.model_name,
                f"{self.config.model_name}:latest"
            ]
            return any(name in model_names for name in search_names)
        except Exception as e:
            logger.error(f"Ollama 모델 확인 실패: {e}")
            return False

    def generate(self, prompt: str) -> str:
        """
        Ollama를 사용한 답변 생성

        Args:
            prompt: 전체 프롬프트

        Returns:
            str: 생성된 답변
        """
        try:
            logger.info(f"Ollama 답변 생성 시작: prompt_length={len(prompt)}")

            response = self.client.generate(
                model=self.config.model_name,
                prompt=prompt,
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens
                }
            )

            answer = response["response"].strip()

            logger.info(
                f"Ollama 답변 생성 완료: answer_length={len(answer)}"
            )

            return answer

        except Exception as e:
            logger.error(f"Ollama 답변 생성 실패: {e}")
            raise ValueError(f"LLM 답변 생성 실패: {e}")

    def health_check(self) -> bool:
        """Ollama 상태 확인"""
        return self._verify_model_exists()
```

---

### 4.3 Step 3: OpenAI Provider 구현 (60분)

#### 작업 내용
**`backend/app/services/llm/openai_provider.py` 작성**:

```python
import os
from openai import OpenAI
from app.services.llm.base_provider import BaseLLMProvider, LLMConfig
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider (GPT-4)"""

    def __init__(self, config: Optional[LLMConfig] = None):
        if config is None:
            config = LLMConfig(
                model_name="gpt-4",
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
        super().__init__(config)

        # OpenAI API Key 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. "
                ".env 파일에 OPENAI_API_KEY를 추가하세요."
            )

        self.client = OpenAI(api_key=api_key)
        logger.info(f"OpenAI Provider 초기화: model={self.config.model_name}")

    def generate(self, prompt: str) -> str:
        """
        OpenAI를 사용한 답변 생성

        Args:
            prompt: 전체 프롬프트

        Returns:
            str: 생성된 답변
        """
        try:
            logger.info(f"OpenAI 답변 생성 시작: prompt_length={len(prompt)}")

            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )

            answer = response.choices[0].message.content.strip()

            logger.info(
                f"OpenAI 답변 생성 완료: answer_length={len(answer)}, "
                f"tokens={response.usage.total_tokens}"
            )

            return answer

        except Exception as e:
            logger.error(f"OpenAI 답변 생성 실패: {e}")
            raise ValueError(f"LLM 답변 생성 실패: {e}")

    def health_check(self) -> bool:
        """OpenAI API 상태 확인"""
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"OpenAI health check 실패: {e}")
            return False
```

---

### 4.4 Step 4: RAG 서비스 구현 (60분)

#### 작업 내용
**`backend/app/services/rag_service.py` 작성**:

```python
import os
from typing import List, Optional
from app.services.llm.base_provider import BaseLLMProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider
from app.services.vector_search import SearchResult
import logging

logger = logging.getLogger(__name__)


# RAG 프롬프트 템플릿
RAG_PROMPT_TEMPLATE = """다음 문서를 참고하여 질문에 답변하세요.

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


class RAGService:
    """RAG (Retrieval-Augmented Generation) 서비스"""

    def __init__(self, provider_type: str = "ollama"):
        """
        Args:
            provider_type: "ollama" 또는 "openai"
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
        검색 결과 기반 답변 생성

        Args:
            query: 사용자 질문
            search_results: 벡터 검색 결과

        Returns:
            str: 생성된 답변
        """
        # Step 1: 검색 결과가 없으면 Fallback
        if not search_results:
            return "죄송합니다. 관련 문서를 찾을 수 없습니다."

        # Step 2: Context 구성
        context = self._build_context(search_results)

        # Step 3: 프롬프트 구성
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context,
            query=query
        )

        logger.info(
            f"RAG 답변 생성 시작: query='{query[:50]}...', "
            f"context_length={len(context)}"
        )

        # Step 4: LLM 답변 생성
        try:
            answer = self.llm_provider.generate(prompt)

            logger.info(
                f"RAG 답변 생성 완료: answer_length={len(answer)}"
            )

            return answer

        except Exception as e:
            logger.error(f"RAG 답변 생성 실패: {e}")
            return "죄송합니다. 답변 생성 중 오류가 발생했습니다."

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
```

---

## 5. 품질 평가 계획

### 5.1 샘플 질문 5개

**`backend/tests/quality/sample_questions.py`**:

```python
SAMPLE_QUESTIONS = [
    {
        "id": "Q1",
        "question": "연차 사용 방법은 어떻게 되나요?",
        "expected_source": "휴가 규정 문서"
    },
    {
        "id": "Q2",
        "question": "급여 지급일은 언제인가요?",
        "expected_source": "급여 규정 문서"
    },
    {
        "id": "Q3",
        "question": "회의실 예약은 어떻게 하나요?",
        "expected_source": "시설 이용 안내"
    },
    {
        "id": "Q4",
        "question": "재택근무 정책이 궁금합니다.",
        "expected_source": "근무 규정 문서"
    },
    {
        "id": "Q5",
        "question": "경조사 휴가는 며칠인가요?",
        "expected_source": "휴가 규정 문서"
    }
]
```

### 5.2 품질 평가 기준

| 기준 | 배점 | 설명 |
|------|------|------|
| 정확도 | 40점 | 질문에 정확한 답변 포함 |
| 출처 명시 | 30점 | 문서 출처 명확히 언급 |
| 유창성 | 20점 | 자연스러운 한국어 |
| 간결성 | 10점 | 3-5문장 이내 |

### 5.3 평가 실행

```bash
# Ollama 평가
pytest backend/tests/quality/test_llm_quality.py --provider=ollama -v

# OpenAI 평가
pytest backend/tests/quality/test_llm_quality.py --provider=openai -v
```

---

## 6. 검증 기준

### 6.1 필수 체크리스트

- [ ] Ollama llama3 답변 생성 성공
- [ ] OpenAI GPT-4 답변 생성 성공
- [ ] 환경 변수만으로 Provider 전환 가능
- [ ] RAG 프롬프트 템플릿 작성
- [ ] 샘플 5개 질문 답변 생성
- [ ] 품질 평가 문서 작성

### 6.2 품질 기준

- [ ] Ollama 평균 점수 ≥ 70점 (100점 만점)
- [ ] OpenAI 평균 점수 ≥ 80점 (100점 만점)

---

## 7. 출력물

### 7.1 생성될 파일

1. `backend/app/services/llm/__init__.py`
2. `backend/app/services/llm/base_provider.py` - LLM Provider 추상 인터페이스
3. `backend/app/services/llm/ollama_provider.py` - Ollama Provider
4. `backend/app/services/llm/openai_provider.py` - OpenAI Provider
5. `backend/app/services/rag_service.py` - RAG 서비스
6. `backend/prompts/rag_prompt.txt` - 프롬프트 템플릿
7. `backend/tests/quality/test_llm_quality.py` - 품질 평가 테스트
8. `docs/llm-quality-evaluation.md` - 품질 평가 리포트

### 7.2 수정될 파일

1. `backend/requirements.txt` - openai 패키지 추가
2. `backend/.env.example` - OPENAI_API_KEY 추가

---

## 8. 참고 문서

- Task Breakdown: `docs/tasks/task-breakdown.md`
- LangChain RAG: https://python.langchain.com/docs/use_cases/question_answering/
- Ollama Python: https://github.com/ollama/ollama-python
- OpenAI API: https://platform.openai.com/docs/api-reference

---

**작성자**: Claude Code (Sonnet 4.5)
**작성일**: 2026-01-03
