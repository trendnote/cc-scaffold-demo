"""
임베딩 서비스 구현

Ollama nomic-embed-text 모델을 사용하여 텍스트 임베딩을 생성합니다.
"""

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

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "nomic-embed-text",
                "expected_dimension": 768,
                "batch_size": 5,
                "max_retries": 3
            }
        }


class EmbeddingServiceError(Exception):
    """임베딩 서비스 기본 에러"""
    pass


class EmbeddingDimensionError(EmbeddingServiceError):
    """임베딩 차원 불일치 에러"""
    pass


class OllamaEmbeddingService:
    """Ollama 임베딩 서비스

    nomic-embed-text 모델을 사용하여 텍스트를 768차원 벡터로 임베딩합니다.
    재시도 로직과 에러 핸들링을 포함합니다.
    """

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Args:
            config: 임베딩 설정 (기본값: nomic-embed-text, 768차원)
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
            response = self.client.list()
            # Ollama SDK 0.4.4+ : ListResponse.models는 Model 객체 리스트
            model_names = [model.model for model in response.models]

            # 모델명에 :latest 태그가 없으면 추가하여 확인
            search_names = [self.config.model_name, f"{self.config.model_name}:latest"]

            if not any(name in model_names for name in search_names):
                raise EmbeddingServiceError(
                    f"Ollama 모델 '{self.config.model_name}'이 없습니다. "
                    f"다음 명령으로 다운로드하세요: "
                    f"ollama pull {self.config.model_name}"
                )

            logger.info(f"Ollama 모델 '{self.config.model_name}' 확인 완료")

        except EmbeddingServiceError:
            raise
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
        if not text or not text.strip():
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
            EmbeddingServiceError: 모든 임베딩 생성 실패 시
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
