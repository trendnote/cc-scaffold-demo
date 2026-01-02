"""
Test Ollama integration with LangChain.

Run: python backend/scripts/test_ollama_integration.py
"""

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
