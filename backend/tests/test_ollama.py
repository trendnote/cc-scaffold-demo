"""
Unit tests for Ollama provider.
"""

import pytest
from app.llm.provider_factory import LLMProviderFactory
from app.llm.ollama_provider import OllamaProvider
import os


@pytest.fixture(scope="function")
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
