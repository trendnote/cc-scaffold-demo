"""
Ollama LLM Provider

Task 2.5a: LLM 기본 답변 생성
"""

from typing import Optional
import ollama
from app.services.llm.base_provider import BaseLLMProvider, LLMConfig
import logging

logger = logging.getLogger(__name__)


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM Provider (llama3)"""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Args:
            config: LLM 설정 (None이면 기본값 사용)
        """
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

        logger.info(f"OllamaProvider 초기화 완료: model={self.config.model_name}")

    def _verify_model_exists(self) -> bool:
        """
        Ollama 모델 존재 확인

        Returns:
            bool: 모델 존재 여부
        """
        try:
            response = self.client.list()
            model_names = [model.model for model in response.models]

            # llama3 또는 llama3:latest 모두 매칭
            search_names = [
                self.config.model_name,
                f"{self.config.model_name}:latest"
            ]

            exists = any(name in model_names for name in search_names)

            if not exists:
                logger.error(
                    f"모델 '{self.config.model_name}' 없음. "
                    f"사용 가능한 모델: {model_names}"
                )

            return exists

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

        Raises:
            ValueError: 답변 생성 실패 시
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
        """
        Ollama 상태 확인

        Returns:
            bool: 정상 동작 여부
        """
        try:
            # 간단한 프롬프트로 동작 확인
            response = self.client.generate(
                model=self.config.model_name,
                prompt="Hello",
                options={"num_predict": 10}
            )

            is_healthy = bool(response.get("response"))

            if is_healthy:
                logger.info("Ollama health check 성공")
            else:
                logger.warning("Ollama health check 실패: 응답 없음")

            return is_healthy

        except Exception as e:
            logger.error(f"Ollama health check 실패: {e}")
            return False
