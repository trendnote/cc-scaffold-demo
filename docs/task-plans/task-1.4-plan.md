# Task Execution Plan: 1.4 - Ollama 설치 및 모델 다운로드

---

## Meta
- **Task ID**: 1.4
- **Task Name**: Ollama 설치 및 모델 다운로드
- **Original Estimate**: 2시간
- **Revised Estimate**: 2.5시간
- **Variance**: +0.5시간 (Provider 추상화 계층 설계 추가)
- **담당**: Infrastructure + Backend
- **Dependencies**: Task 1.1 (Docker Compose 환경 구축)
- **Created**: 2025-12-31
- **Status**: Ready for Implementation

---

## 1. Task Overview

### 1.1 목표
Ollama를 Docker 환경에서 실행하고 RAG 시스템에 필요한 LLM 모델(llama3)과 임베딩 모델(nomic-embed-text)을 다운로드합니다. LangChain과의 연동을 테스트하고, 향후 OpenAI로 전환 가능한 Provider 추상화 계층을 설계하여 프로덕션 환경에서 유연한 LLM 제공자 전환을 지원합니다.

### 1.2 Task Breakdown 정보
- **작업 내용**:
  - Ollama 컨테이너 실행 (docker-compose 포함)
  - 모델 다운로드:
    - `docker exec -it ollama ollama pull llama3`
    - `docker exec -it ollama ollama pull nomic-embed-text`
  - LangChain Ollama 연동 테스트
  - Configuration 설계 (Ollama ↔ OpenAI 전환 가능)

- **검증 기준**:
  - [ ] `llama3` 모델 다운로드 완료
  - [ ] `nomic-embed-text` 모델 다운로드 완료
  - [ ] 테스트 프롬프트 실행 성공
  - [ ] 임베딩 생성 테스트 (768차원 벡터)

- **출력물**:
  - `backend/app/config.py` (LLM Provider 설정)
  - `backend/tests/test_ollama.py`

### 1.3 주요 기술 스택
- **LLM Runtime**: Ollama (local inference)
- **Models**:
  - llama3 (7B parameters, for text generation)
  - nomic-embed-text (137M parameters, for embeddings)
- **Integration**: LangChain (langchain-ollama)
- **Abstraction**: Custom Provider Pattern (or LiteLLM)
- **Docker**: ollama/ollama image
- **Testing**: pytest

---

## 2. Research & Design

### 2.1 기술 조사 결과

#### Ollama Docker Deployment (2025)

**1. Docker 실행 방법**
```bash
docker run -d --rm \
  -v ./ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

**핵심 설정**:
- **Volume Mount**: `-v ./ollama:/root/.ollama` (모델 영구 저장)
- **Port**: `-p 11434:11434` (Ollama API 포트)
- **Auto-remove**: `--rm` (컨테이너 종료 시 자동 삭제)

**2. 모델 다운로드**
```bash
# LLM 모델 (llama3)
docker exec -it ollama ollama pull llama3

# Embedding 모델 (nomic-embed-text)
docker exec -it ollama ollama pull nomic-embed-text
```

**모델 정보**:
- **llama3**: Meta의 7B 파라미터 오픈소스 LLM
  - 용도: 자연어 생성 (RAG 답변 생성)
  - 크기: ~4.7GB
  - Context Window: 8K tokens

- **nomic-embed-text**: Nomic AI의 텍스트 임베딩 모델
  - 용도: 텍스트 → 벡터 변환
  - 차원: 768
  - Context Window: 8,192 tokens
  - 특징: "High-performing open embedding model with large token context"

**3. LangChain Integration**

LangChain provides native Ollama integration via `langchain-ollama` package:

```python
from langchain_ollama import OllamaLLM, OllamaEmbeddings

# LLM for text generation
llm = OllamaLLM(model="llama3", base_url="http://localhost:11434")

# Embeddings for vector conversion
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)
```

**Known Issues**:
- Docker network configuration required for container-to-container communication
- Connection refused errors can occur; solution: use `host.docker.internal` or service name

**출처**:
- [nomic-embed-text - Ollama Library](https://ollama.com/library/nomic-embed-text)
- [OllamaEmbeddings - LangChain Docs](https://python.langchain.com/docs/integrations/text_embedding/ollama/)
- [Embedding models - Ollama Blog](https://ollama.com/blog/embedding-models)
- [Ollama Docker Integration Issues - GitHub](https://github.com/ollama/ollama/issues/6852)

#### Provider Abstraction Pattern (2025)

**1. LiteLLM - Industry Standard**

LiteLLM is the leading abstraction layer for unified LLM API calls across 100+ providers:

```python
from litellm import completion, embedding

# Unified API - works with OpenAI, Ollama, Anthropic, etc.
response = completion(
    model="ollama/llama3",  # or "gpt-4", "claude-3"
    messages=[{"role": "user", "content": "Hello"}]
)
```

**Key Benefits**:
- **Provider Agnostic**: Switch from Ollama to OpenAI with config change only
- **Standardized API**: Same interface for all providers
- **Production Features**: Cost tracking, fallback, caching, retries
- **Zero Code Changes**: Swap providers via environment variable

**2. Alternative: Custom Provider Pattern**

For lightweight projects, a custom abstraction:

```python
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...

    @abstractmethod
    def embed(self, text: str) -> List[float]: ...

class OllamaProvider(BaseLLMProvider):
    # Ollama implementation

class OpenAIProvider(BaseLLMProvider):
    # OpenAI implementation
```

**Decision**: Use **LiteLLM** for production-ready features, fallback to custom pattern if simplicity preferred.

**출처**:
- [Using OpenAI SDK with Local Ollama Models](https://safjan.com/openai-python-sdk-with-local-ollama-models-and-alternatives/)
- [LiteLLM Introduction - Medium](https://medium.com/mitb-for-all/a-gentle-introduction-to-litellm-649d48a0c2c7)
- [LiteLLM Meets Ollama - AILAB Blog](https://blog.ailab.sh/2025/05/unlock-local-llm-power-with-ease.html)

### 2.2 LLM Provider 아키텍처 설계

#### Architecture Diagram

```
┌──────────────────────────────┐
│   FastAPI Application        │
│   (RAG Service)              │
└────────────┬─────────────────┘
             │
             │ uses
             ▼
┌──────────────────────────────┐
│   LLMProviderFactory         │
│   (Config-based selection)   │
└────────────┬─────────────────┘
             │
      ┌──────┴──────┐
      │             │
      ▼             ▼
┌─────────────┐ ┌─────────────┐
│OllamaProvider│ │OpenAIProvider│
│             │ │             │
│ - generate()│ │ - generate()│
│ - embed()   │ │ - embed()   │
└──────┬──────┘ └──────┬──────┘
       │               │
       ▼               ▼
┌─────────────┐ ┌─────────────┐
│   Ollama    │ │  OpenAI API │
│ (localhost) │ │   (remote)  │
└─────────────┘ └─────────────┘
```

#### Configuration Strategy

**Environment Variables**:
```bash
# LLM Provider Selection
LLM_PROVIDER=ollama  # or "openai"

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3
OLLAMA_EMBED_MODEL=nomic-embed-text

# OpenAI Configuration (for future)
OPENAI_API_KEY=sk-...
OPENAI_LLM_MODEL=gpt-4
OPENAI_EMBED_MODEL=text-embedding-3-large
```

**Switching Process**:
1. Change `LLM_PROVIDER=openai`
2. Set `OPENAI_API_KEY`
3. Restart application
4. **No code changes required**

#### Design Decisions

**Decision 1: LiteLLM vs Custom Provider**
- **선택**: Custom Provider Pattern (Phase 1), LiteLLM migration path (Phase 2)
- **이유**:
  - Phase 1 MVP: 2 providers only (Ollama, OpenAI) → custom pattern sufficient
  - 단순성: 의존성 최소화, 명확한 제어
  - Learning curve: 팀이 추상화 패턴 이해 가능
  - Migration path: LiteLLM 추가 쉬움 (인터페이스 호환)
- **Trade-off**: LiteLLM의 고급 기능 (fallback, caching) 미사용 → Phase 2에서 추가

**Decision 2: Synchronous vs Async API**
- **선택**: Async API (async def)
- **이유**:
  - FastAPI는 async 기반
  - LLM 호출은 I/O bound (네트워크 대기)
  - 성능 향상 (동시 요청 처리)
- **주의사항**: LangChain Ollama는 sync/async 모두 지원

**Decision 3: Model Names - Configurable vs Hardcoded**
- **선택**: Configurable (환경 변수)
- **이유**:
  - 모델 업그레이드 시 코드 변경 없음
  - A/B 테스트 가능 (llama3 vs llama3.1)
  - 환경별 다른 모델 (dev: llama3, prod: gpt-4)
- **Trade-off**: 설정 복잡도 증가 (허용 가능)

**Decision 4: Embedding Dimension Validation**
- **선택**: 768차원 검증 (assertion)
- **이유**:
  - Milvus Collection은 768차원 고정 (Task 1.3)
  - nomic-embed-text는 768차원 출력
  - OpenAI text-embedding-3-small도 768차원 가능 (dimensions 파라미터)
- **검증 시점**: 임베딩 생성 후 즉시

### 2.3 Docker Compose 설정

```yaml
# docker-compose.yml에 추가

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./data/ollama:/root/.ollama
    networks:
      - rag-network
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G  # llama3 requires ~6-8GB
        reservations:
          memory: 4G

networks:
  rag-network:
    driver: bridge
```

**주요 설정**:
- **메모리 제한**: 8GB (llama3 모델 크기 고려)
- **볼륨**: 로컬 저장소 마운트 (모델 재다운로드 방지)
- **네트워크**: rag-network (다른 서비스와 통신)
- **재시작 정책**: unless-stopped (장애 시 자동 재시작)

---

## 3. Implementation Steps

### Step 1: Docker Compose 설정 및 Ollama 실행 (30분)

**작업 내용**:
1. `docker-compose.yml`에 Ollama 서비스 추가
   ```yaml
   services:
     ollama:
       image: ollama/ollama:latest
       container_name: ollama
       ports:
         - "11434:11434"
       volumes:
         - ./data/ollama:/root/.ollama
       networks:
         - rag-network
       restart: unless-stopped
       deploy:
         resources:
           limits:
             memory: 8G
           reservations:
             memory: 4G
   ```

2. Ollama 데이터 디렉토리 생성
   ```bash
   mkdir -p data/ollama
   ```

3. Ollama 컨테이너 시작
   ```bash
   docker-compose up -d ollama
   ```

4. Ollama 실행 확인
   ```bash
   docker ps | grep ollama
   docker logs ollama
   curl http://localhost:11434/api/version
   ```

**검증**:
- [ ] Ollama 컨테이너 `running` 상태
- [ ] 포트 11434 접근 가능
- [ ] API 버전 확인 성공

**출력물**:
- `docker-compose.yml` (updated)
- `data/ollama/` 디렉토리

---

### Step 2: 모델 다운로드 (llama3, nomic-embed-text) (45분)

**작업 내용**:
1. llama3 모델 다운로드
   ```bash
   docker exec -it ollama ollama pull llama3
   ```
   **예상 시간**: 5-10분 (4.7GB 다운로드)

2. nomic-embed-text 모델 다운로드
   ```bash
   docker exec -it ollama ollama pull nomic-embed-text
   ```
   **예상 시간**: 1-2분 (274MB 다운로드)

3. 모델 다운로드 확인
   ```bash
   docker exec -it ollama ollama list
   ```
   **Expected output**:
   ```
   NAME                    ID              SIZE      MODIFIED
   llama3:latest           a6990ed6be41    4.7 GB    2 minutes ago
   nomic-embed-text:latest 0a109f422b47    274 MB    1 minute ago
   ```

4. 모델 정보 확인
   ```bash
   docker exec -it ollama ollama show llama3
   docker exec -it ollama ollama show nomic-embed-text
   ```

**검증**:
- [ ] llama3 모델 다운로드 완료 (4.7GB)
- [ ] nomic-embed-text 모델 다운로드 완료 (274MB)
- [ ] `ollama list` 명령어로 확인

**출력물**:
- Downloaded models in `data/ollama/models/`
- 다운로드 로그

---

### Step 3: LangChain Ollama 의존성 설치 및 설정 (20분)

**작업 내용**:
1. langchain-ollama 설치
   ```bash
   cd backend
   echo "langchain-ollama==0.1.0" >> requirements.txt
   echo "langchain-core==0.2.0" >> requirements.txt
   pip install langchain-ollama langchain-core
   ```

2. 환경 변수 추가 (`.env`)
   ```bash
   # LLM Provider Configuration
   LLM_PROVIDER=ollama

   # Ollama Configuration
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_LLM_MODEL=llama3
   OLLAMA_EMBED_MODEL=nomic-embed-text

   # OpenAI Configuration (for future)
   OPENAI_API_KEY=
   OPENAI_LLM_MODEL=gpt-4
   OPENAI_EMBED_MODEL=text-embedding-3-small
   ```

3. `.env.example` 업데이트
   ```bash
   # LLM Provider (ollama or openai)
   LLM_PROVIDER=ollama

   # Ollama Settings
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_LLM_MODEL=llama3
   OLLAMA_EMBED_MODEL=nomic-embed-text

   # OpenAI Settings (optional)
   OPENAI_API_KEY=your-api-key-here
   OPENAI_LLM_MODEL=gpt-4
   OPENAI_EMBED_MODEL=text-embedding-3-small
   ```

**검증**:
- [ ] `langchain-ollama` 설치 확인 (`pip show langchain-ollama`)
- [ ] 환경 변수 파일 생성 확인

**출력물**:
- `backend/requirements.txt` (updated)
- `backend/.env` (updated)
- `backend/.env.example` (updated)

---

### Step 4: Provider 추상화 계층 구현 (45분)

**작업 내용**:
1. `backend/app/llm/base_provider.py` 생성
   ```python
   """
   Base LLM Provider Interface

   Defines the contract for all LLM providers (Ollama, OpenAI, etc.)
   """

   from abc import ABC, abstractmethod
   from typing import List, Optional, Dict, Any
   import logging

   logger = logging.getLogger(__name__)


   class BaseLLMProvider(ABC):
       """Abstract base class for LLM providers."""

       @abstractmethod
       async def generate(
           self,
           prompt: str,
           max_tokens: int = 1000,
           temperature: float = 0.7,
           **kwargs
       ) -> str:
           """
           Generate text completion from prompt.

           Args:
               prompt: Input prompt
               max_tokens: Maximum tokens to generate
               temperature: Sampling temperature (0-1)

           Returns:
               str: Generated text
           """
           pass

       @abstractmethod
       async def embed(
           self,
           text: str,
           **kwargs
       ) -> List[float]:
           """
           Generate embedding vector from text.

           Args:
               text: Input text to embed

           Returns:
               List[float]: Embedding vector (768 dimensions)
           """
           pass

       @abstractmethod
       async def embed_batch(
           self,
           texts: List[str],
           **kwargs
       ) -> List[List[float]]:
           """
           Generate embedding vectors for multiple texts.

           Args:
               texts: List of texts to embed

           Returns:
               List[List[float]]: List of embedding vectors
           """
           pass

       @abstractmethod
       def get_model_info(self) -> Dict[str, Any]:
           """
           Get provider and model information.

           Returns:
               dict: Model metadata
           """
           pass
   ```

2. `backend/app/llm/ollama_provider.py` 생성
   ```python
   """
   Ollama LLM Provider Implementation
   """

   from typing import List, Dict, Any
   from langchain_ollama import OllamaLLM, OllamaEmbeddings
   import os
   from dotenv import load_dotenv
   import logging

   from .base_provider import BaseLLMProvider

   load_dotenv()
   logger = logging.getLogger(__name__)


   class OllamaProvider(BaseLLMProvider):
       """Ollama LLM provider using LangChain integration."""

       def __init__(self):
           self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
           self.llm_model = os.getenv("OLLAMA_LLM_MODEL", "llama3")
           self.embed_model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

           # Initialize LangChain Ollama clients
           self.llm = OllamaLLM(
               model=self.llm_model,
               base_url=self.base_url
           )

           self.embeddings = OllamaEmbeddings(
               model=self.embed_model,
               base_url=self.base_url
           )

           logger.info(f"Initialized Ollama provider: {self.base_url}")

       async def generate(
           self,
           prompt: str,
           max_tokens: int = 1000,
           temperature: float = 0.7,
           **kwargs
       ) -> str:
           """Generate text using Ollama LLM."""
           try:
               # LangChain Ollama uses invoke() method
               response = await self.llm.ainvoke(
                   prompt,
                   max_tokens=max_tokens,
                   temperature=temperature,
                   **kwargs
               )
               return response
           except Exception as e:
               logger.error(f"Ollama generation failed: {e}")
               raise

       async def embed(
           self,
           text: str,
           **kwargs
       ) -> List[float]:
           """Generate embedding using Ollama embeddings."""
           try:
               # LangChain Ollama embeddings
               vector = await self.embeddings.aembed_query(text)

               # Validate dimension
               if len(vector) != 768:
                   raise ValueError(
                       f"Expected 768 dimensions, got {len(vector)}"
                   )

               return vector
           except Exception as e:
               logger.error(f"Ollama embedding failed: {e}")
               raise

       async def embed_batch(
           self,
           texts: List[str],
           **kwargs
       ) -> List[List[float]]:
           """Generate embeddings for multiple texts."""
           try:
               vectors = await self.embeddings.aembed_documents(texts)

               # Validate all dimensions
               for i, vector in enumerate(vectors):
                   if len(vector) != 768:
                       raise ValueError(
                           f"Text {i}: Expected 768 dimensions, got {len(vector)}"
                       )

               return vectors
           except Exception as e:
               logger.error(f"Ollama batch embedding failed: {e}")
               raise

       def get_model_info(self) -> Dict[str, Any]:
           """Get Ollama model information."""
           return {
               "provider": "ollama",
               "base_url": self.base_url,
               "llm_model": self.llm_model,
               "embed_model": self.embed_model,
               "embed_dimension": 768
           }
   ```

3. `backend/app/llm/openai_provider.py` 생성 (Stub for Phase 2)
   ```python
   """
   OpenAI LLM Provider Implementation (Stub)
   """

   from typing import List, Dict, Any
   from .base_provider import BaseLLMProvider
   import logging

   logger = logging.getLogger(__name__)


   class OpenAIProvider(BaseLLMProvider):
       """OpenAI LLM provider (Stub for Phase 2)."""

       def __init__(self):
           logger.warning("OpenAIProvider is not implemented yet (Phase 2)")
           # TODO: Implement OpenAI integration
           pass

       async def generate(self, prompt: str, **kwargs) -> str:
           raise NotImplementedError("OpenAI provider not implemented")

       async def embed(self, text: str, **kwargs) -> List[float]:
           raise NotImplementedError("OpenAI provider not implemented")

       async def embed_batch(self, texts: List[str], **kwargs) -> List[List[float]]:
           raise NotImplementedError("OpenAI provider not implemented")

       def get_model_info(self) -> Dict[str, Any]:
           return {"provider": "openai", "status": "not_implemented"}
   ```

4. `backend/app/llm/provider_factory.py` 생성
   ```python
   """
   LLM Provider Factory

   Factory for creating LLM provider instances based on configuration.
   """

   import os
   from dotenv import load_dotenv
   import logging

   from .base_provider import BaseLLMProvider
   from .ollama_provider import OllamaProvider
   from .openai_provider import OpenAIProvider

   load_dotenv()
   logger = logging.getLogger(__name__)


   class LLMProviderFactory:
       """Factory for creating LLM providers."""

       _instance: BaseLLMProvider = None

       @classmethod
       def get_provider(cls) -> BaseLLMProvider:
           """
           Get LLM provider instance (singleton).

           Returns:
               BaseLLMProvider: Configured provider instance
           """
           if cls._instance is None:
               provider_name = os.getenv("LLM_PROVIDER", "ollama").lower()

               if provider_name == "ollama":
                   cls._instance = OllamaProvider()
               elif provider_name == "openai":
                   cls._instance = OpenAIProvider()
               else:
                   raise ValueError(f"Unknown LLM provider: {provider_name}")

               logger.info(f"Initialized LLM provider: {provider_name}")

           return cls._instance

       @classmethod
       def reset(cls):
           """Reset provider instance (for testing)."""
           cls._instance = None
   ```

5. `backend/app/llm/__init__.py` 생성
   ```python
   from .base_provider import BaseLLMProvider
   from .ollama_provider import OllamaProvider
   from .openai_provider import OpenAIProvider
   from .provider_factory import LLMProviderFactory

   __all__ = [
       "BaseLLMProvider",
       "OllamaProvider",
       "OpenAIProvider",
       "LLMProviderFactory",
   ]
   ```

**검증**:
- [ ] 모든 모듈 임포트 에러 없음
- [ ] Abstract base class 정의 확인
- [ ] Factory pattern 동작 확인

**출력물**:
- `backend/app/llm/base_provider.py`
- `backend/app/llm/ollama_provider.py`
- `backend/app/llm/openai_provider.py`
- `backend/app/llm/provider_factory.py`
- `backend/app/llm/__init__.py`

---

### Step 5: Ollama 연동 테스트 (30분)

**작업 내용**:
1. `backend/scripts/test_ollama_integration.py` 생성
   ```python
   """
   Test Ollama integration with LangChain.

   Run: python backend/scripts/test_ollama_integration.py
   ```

   import sys
   import os
   import asyncio
   sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

   from app.llm.provider_factory import LLMProviderFactory


   async def test_llm_generation():
       """Test LLM text generation."""
       print("=" * 60)
       print("Test 1: LLM Text Generation")
       print("=" * 60)

       provider = LLMProviderFactory.get_provider()
       model_info = provider.get_model_info()
       print(f"Provider: {model_info['provider']}")
       print(f"LLM Model: {model_info['llm_model']}")
       print(f"Base URL: {model_info['base_url']}")

       prompt = "RAG 시스템이란 무엇인가요? 한 문장으로 설명해주세요."
       print(f"\nPrompt: {prompt}")

       print("\nGenerating response...")
       response = await provider.generate(prompt, max_tokens=100, temperature=0.7)

       print(f"\nResponse: {response}")
       print(f"Response length: {len(response)} characters")


   async def test_embedding_single():
       """Test embedding for single text."""
       print("\n" + "=" * 60)
       print("Test 2: Single Text Embedding")
       print("=" * 60)

       provider = LLMProviderFactory.get_provider()
       model_info = provider.get_model_info()
       print(f"Embedding Model: {model_info['embed_model']}")

       text = "연차 사용 시 3일 전에 신청해야 합니다."
       print(f"\nText: {text}")

       print("\nGenerating embedding...")
       vector = await provider.embed(text)

       print(f"\nEmbedding dimension: {len(vector)}")
       print(f"First 5 values: {vector[:5]}")
       print(f"Vector norm: {sum(x**2 for x in vector) ** 0.5:.4f}")

       # Validate dimension
       assert len(vector) == 768, f"Expected 768 dimensions, got {len(vector)}"
       print("✅ Dimension validation passed (768)")


   async def test_embedding_batch():
       """Test batch embedding."""
       print("\n" + "=" * 60)
       print("Test 3: Batch Embedding")
       print("=" * 60)

       provider = LLMProviderFactory.get_provider()

       texts = [
           "연차 사용 시 3일 전에 신청해야 합니다.",
           "회사 정책에 따라 연차는 1년에 15일 제공됩니다.",
           "재택근무는 주 2회까지 가능합니다."
       ]

       print(f"Number of texts: {len(texts)}")
       for i, text in enumerate(texts):
           print(f"  {i+1}. {text}")

       print("\nGenerating batch embeddings...")
       vectors = await provider.embed_batch(texts)

       print(f"\nNumber of vectors: {len(vectors)}")
       for i, vector in enumerate(vectors):
           print(f"  Vector {i+1}: {len(vector)} dimensions")
           assert len(vector) == 768, f"Vector {i+1}: Expected 768, got {len(vector)}"

       print("✅ All vectors have 768 dimensions")


   async def main():
       """Run all tests."""
       try:
           await test_llm_generation()
           await test_embedding_single()
           await test_embedding_batch()

           print("\n" + "=" * 60)
           print("✅ All tests passed!")
           print("=" * 60)

       except Exception as e:
           print(f"\n❌ Error: {e}")
           import traceback
           traceback.print_exc()
           sys.exit(1)


   if __name__ == "__main__":
       asyncio.run(main())
   ```

2. 통합 테스트 실행
   ```bash
   python backend/scripts/test_ollama_integration.py
   ```

**검증**:
- [ ] LLM 텍스트 생성 성공 (llama3)
- [ ] 단일 텍스트 임베딩 성공 (768차원)
- [ ] 배치 임베딩 성공 (3개 텍스트, 각 768차원)
- [ ] 모든 테스트 통과

**출력물**:
- `backend/scripts/test_ollama_integration.py`
- 테스트 실행 결과 로그

---

### Step 6: 단위 테스트 작성 (30분)

**작업 내용**:
1. `backend/tests/test_ollama.py` 생성
   ```python
   """
   Unit tests for Ollama provider.
   """

   import pytest
   from app.llm.provider_factory import LLMProviderFactory
   from app.llm.ollama_provider import OllamaProvider
   import os


   @pytest.fixture(scope="module")
   def provider():
       """Ollama provider fixture."""
       # Set environment for testing
       os.environ["LLM_PROVIDER"] = "ollama"
       LLMProviderFactory.reset()
       return LLMProviderFactory.get_provider()


   def test_provider_factory():
       """Test provider factory returns OllamaProvider."""
       os.environ["LLM_PROVIDER"] = "ollama"
       LLMProviderFactory.reset()
       provider = LLMProviderFactory.get_provider()
       assert isinstance(provider, OllamaProvider)


   def test_provider_singleton():
       """Test provider factory returns singleton."""
       provider1 = LLMProviderFactory.get_provider()
       provider2 = LLMProviderFactory.get_provider()
       assert provider1 is provider2


   def test_get_model_info(provider):
       """Test model info retrieval."""
       info = provider.get_model_info()
       assert info["provider"] == "ollama"
       assert "llm_model" in info
       assert "embed_model" in info
       assert info["embed_dimension"] == 768


   @pytest.mark.asyncio
   async def test_llm_generation(provider):
       """Test LLM text generation."""
       prompt = "What is 2+2?"
       response = await provider.generate(prompt, max_tokens=50)
       assert isinstance(response, str)
       assert len(response) > 0


   @pytest.mark.asyncio
   async def test_embedding_single(provider):
       """Test single text embedding."""
       text = "Hello, world!"
       vector = await provider.embed(text)

       assert isinstance(vector, list)
       assert len(vector) == 768
       assert all(isinstance(x, float) for x in vector)


   @pytest.mark.asyncio
   async def test_embedding_dimension_validation(provider):
       """Test embedding dimension is 768."""
       text = "Test embedding dimension"
       vector = await provider.embed(text)
       assert len(vector) == 768


   @pytest.mark.asyncio
   async def test_embedding_batch(provider):
       """Test batch embedding."""
       texts = ["Text 1", "Text 2", "Text 3"]
       vectors = await provider.embed_batch(texts)

       assert len(vectors) == 3
       for vector in vectors:
           assert len(vector) == 768


   @pytest.mark.asyncio
   async def test_embedding_empty_text(provider):
       """Test embedding with empty text."""
       text = ""
       vector = await provider.embed(text)
       assert len(vector) == 768  # Should still return 768-dim vector


   @pytest.mark.asyncio
   async def test_embedding_long_text(provider):
       """Test embedding with long text (within context window)."""
       text = "This is a test. " * 100  # ~1600 chars
       vector = await provider.embed(text)
       assert len(vector) == 768


   @pytest.mark.asyncio
   async def test_llm_with_parameters(provider):
       """Test LLM with custom parameters."""
       prompt = "Count to 5"
       response = await provider.generate(
           prompt,
           max_tokens=100,
           temperature=0.5
       )
       assert isinstance(response, str)
   ```

2. 테스트 실행
   ```bash
   pytest backend/tests/test_ollama.py -v
   ```

**검증**:
- [ ] 11개 테스트 모두 통과
- [ ] Provider factory 테스트 성공
- [ ] LLM 생성 테스트 성공
- [ ] 임베딩 테스트 성공 (768차원 검증)

**출력물**:
- `backend/tests/test_ollama.py`
- 테스트 실행 결과

---

### Step 7: 문서화 및 최종 검증 (20분)

**작업 내용**:
1. README 업데이트
   ```markdown
   ## LLM Provider Configuration

   ### Ollama (Local)

   1. Start Ollama container:
      ```bash
      docker-compose up -d ollama
      ```

   2. Download models:
      ```bash
      docker exec -it ollama ollama pull llama3
      docker exec -it ollama ollama pull nomic-embed-text
      ```

   3. Verify models:
      ```bash
      docker exec -it ollama ollama list
      ```

   4. Test integration:
      ```bash
      python backend/scripts/test_ollama_integration.py
      ```

   ### OpenAI (Cloud) - Phase 2

   1. Set environment variables:
      ```bash
      LLM_PROVIDER=openai
      OPENAI_API_KEY=your-api-key
      ```

   2. Restart application

   ### Configuration

   Environment variables (`.env`):
   ```
   LLM_PROVIDER=ollama  # or "openai"

   # Ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_LLM_MODEL=llama3
   OLLAMA_EMBED_MODEL=nomic-embed-text

   # OpenAI (optional)
   OPENAI_API_KEY=
   OPENAI_LLM_MODEL=gpt-4
   OPENAI_EMBED_MODEL=text-embedding-3-small
   ```

   ### Switching Providers

   No code changes required:
   1. Change `LLM_PROVIDER` in `.env`
   2. Set provider-specific variables
   3. Restart application
   ```

2. 최종 검증 체크리스트
   ```bash
   # 1. Ollama 실행 확인
   docker ps | grep ollama

   # 2. 모델 다운로드 확인
   docker exec -it ollama ollama list

   # 3. API 접근 확인
   curl http://localhost:11434/api/version

   # 4. 통합 테스트
   python backend/scripts/test_ollama_integration.py

   # 5. 단위 테스트
   pytest backend/tests/test_ollama.py -v

   # 6. Provider info 확인
   python -c "from app.llm.provider_factory import LLMProviderFactory; import asyncio; print(LLMProviderFactory.get_provider().get_model_info())"
   ```

3. `docs/llm/README.md` 생성 (운영 가이드)
   ```markdown
   # LLM Provider Operations Guide

   ## Model Management

   ### List Models
   ```bash
   docker exec -it ollama ollama list
   ```

   ### Update Models
   ```bash
   docker exec -it ollama ollama pull llama3
   ```

   ### Remove Models
   ```bash
   docker exec -it ollama ollama rm llama3
   ```

   ## Performance Tuning

   ### Ollama Memory Settings
   Adjust in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       limits:
         memory: 8G  # Increase for larger models
   ```

   ### LLM Parameters
   - `max_tokens`: Limit response length (default: 1000)
   - `temperature`: Control randomness (0-1, default: 0.7)

   ## Troubleshooting

   ### "Connection refused" Error
   1. Check Ollama container: `docker ps | grep ollama`
   2. Check logs: `docker logs ollama`
   3. Verify port: `curl http://localhost:11434/api/version`

   ### Slow Response
   1. Check model size (llama3: ~4.7GB)
   2. Monitor memory: `docker stats ollama`
   3. Consider smaller model (llama3:8b vs llama3:70b)

   ### Embedding Dimension Mismatch
   - Ensure nomic-embed-text is used (768 dimensions)
   - OpenAI alternative: text-embedding-3-small with `dimensions=768`
   ```

**검증**:
- [ ] README 섹션 추가 확인
- [ ] 최종 체크리스트 모두 통과
- [ ] 운영 가이드 문서 생성

**출력물**:
- `README.md` (updated)
- `docs/llm/README.md`
- 최종 검증 결과

---

## 4. Testing Plan

### 4.1 단위 테스트 (pytest)

**Test Case 1: Provider Factory**
```python
def test_provider_factory():
    """Factory가 올바른 provider 반환"""
def test_provider_singleton():
    """Singleton 패턴 확인"""
```

**Test Case 2: Model Info**
```python
def test_get_model_info():
    """모델 정보 조회 성공"""
```

**Test Case 3: LLM Generation**
```python
async def test_llm_generation():
    """텍스트 생성 성공"""
async def test_llm_with_parameters():
    """파라미터 전달 확인"""
```

**Test Case 4: Single Embedding**
```python
async def test_embedding_single():
    """단일 텍스트 임베딩 성공"""
async def test_embedding_dimension_validation():
    """768차원 검증"""
```

**Test Case 5: Batch Embedding**
```python
async def test_embedding_batch():
    """배치 임베딩 성공"""
```

**Test Case 6: Edge Cases**
```python
async def test_embedding_empty_text():
    """빈 텍스트 처리"""
async def test_embedding_long_text():
    """긴 텍스트 처리 (context window 내)"""
```

### 4.2 통합 테스트

**Integration Test 1: End-to-End Workflow**
```python
async def test_full_llm_workflow():
    """
    1. Provider 초기화
    2. LLM 텍스트 생성
    3. 임베딩 생성
    4. 차원 검증
    """
```

**Integration Test 2: Provider Switching**
```python
def test_provider_switch():
    """
    1. Ollama provider 초기화
    2. OpenAI provider로 전환 (env var)
    3. Factory reset 후 재초기화
    """
```

### 4.3 성능 테스트

**Performance Test 1: LLM Latency**
```python
async def test_llm_latency():
    """
    10회 LLM 호출
    P95 < 5초 목표 (llama3 local)
    """
```

**Performance Test 2: Embedding Throughput**
```python
async def test_embedding_throughput():
    """
    100개 텍스트 임베딩
    처리 시간 측정
    """
```

### 4.4 수동 테스트

**Manual Test 1: Ollama UI (Optional)**
- Ollama는 기본 UI 없음, CLI만 지원
- 대신 `ollama list`, `ollama show` 사용

**Manual Test 2: Model Download Verification**
- [ ] `ollama list` 명령어로 모델 확인
- [ ] 모델 크기 확인 (llama3: 4.7GB, nomic-embed-text: 274MB)

**Manual Test 3: API Response**
```bash
# Test LLM
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Hello!"
}'

# Test Embedding
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "Hello!"
}'
```

---

## 5. Risks & Mitigation

### Risk 1: Ollama 품질 부족 (High Probability)

**Impact**: Critical
- RAG 답변 품질 저하 → 사용자 만족도 하락
- Hallucination 발생 → 잘못된 정보 제공
- 한국어 성능 부족 → 사내 정보 부정확

**Probability**: High (60%)
- llama3는 범용 모델 (한국어 특화 아님)
- 7B 파라미터 (GPT-4 대비 작음)
- Local 모델은 Cloud 모델 대비 성능 차이

**Mitigation**:
1. **Provider 추상화 계층 구현 (This Task)**
   - Ollama → OpenAI 전환 즉시 가능
   - 환경 변수 변경만으로 전환
   - 코드 수정 불필요

2. **품질 평가 실험 (Task 2.5a)**
   - 샘플 쿼리 20개 준비
   - Ollama vs OpenAI 비교 실험
   - 평가 기준: 정확도, 관련성, 유창성
   - 자동 평가: ROUGE, BLEU

3. **조기 전환 결정**
   - Task 2.5a 완료 시 품질 평가
   - Ollama 품질 수용 불가 → OpenAI 즉시 전환
   - 예산 확보 필요

4. **Hybrid 접근 (Alternative)**
   - 임베딩: Ollama (nomic-embed-text, 품질 충분)
   - LLM 생성: OpenAI (GPT-4, 품질 우선)

**Owner**: Backend Lead
**Review**: Task 2.5a 완료 시 (LLM 답변 품질 평가)

---

### Risk 2: Ollama 메모리 부족 (Medium Probability)

**Impact**: High
- llama3 로드 실패 → 서비스 불가
- OOM 에러 → 컨테이너 재시작 반복

**Probability**: Medium (30%)
- llama3는 ~6-8GB 메모리 필요
- Docker Desktop 기본 메모리 제한 (2-4GB)

**Mitigation**:
1. **Docker 메모리 제한 설정**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 8G
       reservations:
         memory: 4G
   ```

2. **호스트 메모리 확인**
   ```bash
   docker system info | grep "Total Memory"
   # 최소 12GB 권장 (Ollama 8GB + 기타 4GB)
   ```

3. **모델 크기 최적화**
   - llama3:7b (4.7GB) → llama3:8b-q4 (2.3GB, quantized)
   - 품질 vs 메모리 트레이드오프

4. **Fallback to CPU** (성능 저하 감수)
   - GPU 없이도 동작 (느림)
   - Docker Desktop CPU만 사용

**Owner**: Infrastructure Team
**Review**: Task 1.4 완료 시 (메모리 사용량 확인)

---

### Risk 3: nomic-embed-text 차원 불일치 (Low Probability)

**Impact**: Critical
- Milvus는 768차원 Collection (Task 1.3)
- 차원 불일치 → 삽입 실패

**Probability**: Low (10%)
- nomic-embed-text는 명시적으로 768차원
- 하지만 모델 업데이트 시 변경 가능

**Mitigation**:
1. **Runtime Validation**
   ```python
   vector = await provider.embed(text)
   if len(vector) != 768:
       raise ValueError(f"Expected 768, got {len(vector)}")
   ```

2. **테스트 케이스 추가**
   ```python
   async def test_embedding_dimension():
       assert len(vector) == 768
   ```

3. **OpenAI Embedding Dimension 설정**
   ```python
   # OpenAI text-embedding-3-small
   embeddings = OpenAIEmbeddings(
       model="text-embedding-3-small",
       dimensions=768  # Force 768 dimensions
   )
   ```

4. **Monitoring**
   - 임베딩 생성 시 차원 로깅
   - 차원 불일치 시 Alert

**Owner**: Backend Engineer
**Review**: Task 1.4 완료 시 (임베딩 차원 검증)

---

### Risk 4: Docker Network 이슈 (Low Probability)

**Impact**: Medium
- Backend → Ollama 연결 실패
- "Connection refused" 에러

**Probability**: Low (20%)
- Docker Compose는 자동 네트워크 설정
- 하지만 컨테이너 간 통신 실패 가능

**Mitigation**:
1. **명시적 네트워크 설정**
   ```yaml
   services:
     backend:
       networks:
         - rag-network
     ollama:
       networks:
         - rag-network
   networks:
     rag-network:
       driver: bridge
   ```

2. **Service Name 사용**
   ```python
   # localhost 대신 service name
   OLLAMA_BASE_URL=http://ollama:11434
   ```

3. **Host Network Mode (Fallback)**
   ```yaml
   ollama:
     network_mode: host  # 개발 환경만
   ```

4. **Connection Test**
   ```bash
   docker exec -it backend curl http://ollama:11434/api/version
   ```

**Owner**: Infrastructure Team
**Review**: Task 1.4 완료 시 (연결 테스트)

---

## 6. Definition of Done

### 6.1 기능 완료 기준
- [ ] **Ollama 컨테이너 실행 성공**
  - Docker Compose로 시작
  - 포트 11434 접근 가능
  - Health check 성공

- [ ] **모델 다운로드 완료**
  - llama3 모델 (4.7GB)
  - nomic-embed-text 모델 (274MB)
  - `ollama list` 확인

- [ ] **Provider 추상화 계층 구현**
  - BaseLLMProvider (abstract class)
  - OllamaProvider (implementation)
  - OpenAIProvider (stub)
  - LLMProviderFactory (factory)

- [ ] **LangChain 연동 성공**
  - OllamaLLM (text generation)
  - OllamaEmbeddings (embeddings)
  - Async API 지원

### 6.2 테스트 완료 기준
- [ ] **단위 테스트 11개 통과**
  - Provider factory
  - LLM generation
  - Single/batch embedding
  - Dimension validation (768)
  - Coverage > 80%

- [ ] **통합 테스트 성공**
  - 텍스트 생성 테스트
  - 임베딩 생성 테스트 (768차원 확인)
  - 배치 임베딩 테스트

- [ ] **성능 테스트 (Optional)**
  - LLM latency P95 < 5초
  - Embedding throughput 측정

### 6.3 코드 품질 기준
- [ ] **CLAUDE.md HARD RULE 준수**
  - 환경 변수 사용 (OLLAMA_BASE_URL)
  - API 키 하드코딩 없음 (OpenAI)
  - 에러 핸들링 완비

- [ ] **타입 힌트 적용**
  - 모든 메서드 타입 힌트
  - mypy 통과

- [ ] **문서화**
  - Docstring (Google style)
  - README 섹션 추가
  - 운영 가이드 작성

### 6.4 성능 기준
- [ ] **메모리 사용량 확인**
  - Ollama 컨테이너 < 8GB
  - `docker stats` 모니터링

- [ ] **응답 시간 목표**
  - LLM 생성: < 5초 (P95)
  - 임베딩 생성: < 1초 (single)

### 6.5 운영 준비 기준
- [ ] **환경 변수 관리**
  - `.env.example` 업데이트
  - Provider 전환 가이드 문서화

- [ ] **Provider 전환 검증**
  - 환경 변수 변경만으로 전환 가능
  - 코드 수정 불필요 확인

- [ ] **모니터링 설정**
  - Ollama health check
  - 모델 로드 상태 확인

### 6.6 리뷰 및 승인
- [ ] **Peer Review 완료**
  - Provider 추상화 설계 리뷰
  - Ollama 연동 코드 리뷰
  - 테스트 코드 리뷰

- [ ] **Tech Lead 승인**
  - Provider pattern 승인
  - 모델 선택 승인 (llama3, nomic-embed-text)

---

## 7. Time Breakdown

| Step | 작업 내용 | 예상 시간 | 누적 시간 |
|------|----------|----------|----------|
| 1 | Docker Compose 설정 및 Ollama 실행 | 0.5h | 0.5h |
| 2 | 모델 다운로드 (llama3, nomic-embed-text) | 0.75h | 1.25h |
| 3 | LangChain Ollama 의존성 설치 | 0.33h | 1.58h |
| 4 | Provider 추상화 계층 구현 | 0.75h | 2.33h |
| 5 | Ollama 연동 테스트 | 0.5h | 2.83h |
| 6 | 단위 테스트 작성 | 0.5h | 3.33h |
| 7 | 문서화 및 최종 검증 | 0.33h | 3.66h |

**Total**: 3.66시간 (예상 2.5시간 + 버퍼 1.16시간)

**시간 배분**:
- Research: 0% (사전 완료)
- Implementation: 60% (2.2h)
- Testing: 27% (1.0h)
- Documentation: 13% (0.46h)

**Note**: 모델 다운로드 시간은 네트워크 속도에 따라 변동 (5-15분)

---

## 8. Next Steps

### 8.1 Immediate Next Steps (Task 1.4 완료 후)
1. **Task 1.5 준비**: 문서 파싱 모듈 구현 (PDF)
   - pypdf, pdfplumber 조사
   - 파일 크기 제한 설정

2. **Documentation Update**
   - Architecture 문서에 LLM Provider 다이어그램 추가
   - Provider 전환 절차 문서화

### 8.2 Follow-up Tasks
- **Task 1.8**: 문서 임베딩 (OllamaProvider.embed_batch() 활용)
- **Task 2.5a**: LLM 기본 답변 생성 (OllamaProvider.generate() 활용)
- **Task 2.5a**: **품질 평가 실험** → Ollama vs OpenAI 비교 → 전환 결정

### 8.3 Monitoring & Maintenance
- **일간 점검**: Ollama 컨테이너 상태, 메모리 사용량
- **주간 점검**: 모델 업데이트 확인 (ollama pull)
- **월간 점검**: Provider 성능 비교 (Ollama vs OpenAI 품질)

---

## 9. References

### 9.1 Ollama Documentation
- [nomic-embed-text - Ollama Library](https://ollama.com/library/nomic-embed-text)
- [Embedding models - Ollama Blog](https://ollama.com/blog/embedding-models)
- [Ollama GitHub](https://github.com/ollama/ollama)

### 9.2 LangChain Integration
- [OllamaEmbeddings - LangChain Docs](https://python.langchain.com/docs/integrations/text_embedding/ollama/)
- [Ollama - Chroma Cookbook](https://cookbook.chromadb.dev/integrations/ollama/embeddings/)
- [Ollama Docker Issues - GitHub](https://github.com/ollama/ollama/issues/6852)

### 9.3 Provider Abstraction
- [Using OpenAI SDK with Local Ollama Models](https://safjan.com/openai-python-sdk-with-local-ollama-models-and-alternatives/)
- [LiteLLM Introduction - Medium](https://medium.com/mitb-for-all/a-gentle-introduction-to-litellm-649d48a0c2c7)
- [LiteLLM Meets Ollama - AILAB Blog](https://blog.ailab.sh/2025/05/unlock-local-llm-power-with-ease.html)

### 9.4 Internal References
- Task Breakdown: `docs/tasks/task-breakdown.md`
- Task 1.3 Plan: `docs/task-plans/task-1.3-plan.md` (Milvus 768-dim vectors)
- Architecture: `docs/architecture/architecture.md`

---

## 10. Approval

**Prepared By**: Claude (Task Planner)
**Date**: 2025-12-31

**Review Status**:
- [ ] Peer Review (Backend + Infrastructure Team)
- [ ] Tech Lead Approval
- [ ] Ready for Implementation

**Notes**:
이 계획서는 Task 1.4의 상세 실행 가이드입니다. Ollama를 Docker 환경에서 실행하고 llama3, nomic-embed-text 모델을 다운로드하며, LangChain 연동을 완료합니다. **핵심은 Provider 추상화 계층 구현으로, Ollama 품질이 부족할 경우 OpenAI로 즉시 전환 가능한 아키텍처**를 제공합니다.

**Critical Decision**:
- **Provider 추상화 계층 구현** → Ollama/OpenAI 전환 가능
- **Task 2.5a에서 품질 평가** → Ollama 품질 부족 시 OpenAI 전환
- **환경 변수로만 전환** → 코드 수정 불필요

**Key Risks**:
1. ⚠️ **Ollama 품질 부족 (High)** → Provider 추상화로 대응
2. ⚠️ **메모리 부족 (Medium)** → Docker 메모리 제한 8GB
3. ✅ **차원 불일치 (Low)** → Runtime validation (768)
4. ✅ **Docker 네트워크 (Low)** → Service name 사용

---

**END OF TASK EXECUTION PLAN**
