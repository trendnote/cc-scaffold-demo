"""
OpenAI LLM Provider

Task 2.5a: LLM 기본 답변 생성
"""

import os
from typing import Optional
from openai import OpenAI
from app.services.llm.base_provider import BaseLLMProvider, LLMConfig
import logging

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM Provider (GPT-4)"""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Args:
            config: LLM 설정 (None이면 기본값 사용)

        Raises:
            ValueError: OPENAI_API_KEY 환경 변수가 없을 때
        """
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

        Raises:
            ValueError: 답변 생성 실패 시
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
        """
        OpenAI API 상태 확인

        Returns:
            bool: 정상 동작 여부
        """
        try:
            # 모델 리스트 확인으로 API 상태 검증
            self.client.models.list()
            logger.info("OpenAI health check 성공")
            return True

        except Exception as e:
            logger.error(f"OpenAI health check 실패: {e}")
            return False
