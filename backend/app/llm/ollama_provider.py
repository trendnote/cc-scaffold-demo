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
            # Create LLM instance with specific parameters
            # Ollama uses num_predict instead of max_tokens
            llm = OllamaLLM(
                model=self.llm_model,
                base_url=self.base_url,
                num_predict=max_tokens,
                temperature=temperature,
                **kwargs
            )

            # LangChain Ollama uses invoke() method
            response = await llm.ainvoke(prompt)
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
