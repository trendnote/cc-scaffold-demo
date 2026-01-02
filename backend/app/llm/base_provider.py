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
