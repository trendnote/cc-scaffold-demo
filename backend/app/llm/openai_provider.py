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
