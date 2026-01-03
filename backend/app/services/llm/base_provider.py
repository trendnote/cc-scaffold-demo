"""
LLM Provider 추상 베이스 클래스

Task 2.5a: LLM 기본 답변 생성
"""

from abc import ABC, abstractmethod
from typing import Optional
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
        """
        Args:
            config: LLM 설정
        """
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
            ValueError: 답변 생성 실패 시
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Provider 상태 확인

        Returns:
            bool: 정상 동작 여부
        """
        pass
