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
