"""
임베딩 서비스 테스트

OllamaEmbeddingService의 동작을 검증합니다.
"""

import pytest
from app.services.embedding_service import (
    OllamaEmbeddingService,
    EmbeddingConfig,
    EmbeddingServiceError,
    EmbeddingDimensionError,
)


@pytest.fixture
def embedding_service():
    """임베딩 서비스 픽스처"""
    return OllamaEmbeddingService()


# ============================================================================
# Happy Path Tests
# ============================================================================

def test_service_initialization(embedding_service):
    """TC01: 서비스 초기화 검증"""
    assert embedding_service is not None
    assert embedding_service.config.model_name == "nomic-embed-text"
    assert embedding_service.config.expected_dimension == 768


def test_single_text_embedding(embedding_service):
    """TC02: 단일 텍스트 임베딩 생성"""
    text = "This is a test sentence for embedding."

    embedding = embedding_service.embed_text(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)
    # 0이 아닌 값들이 있어야 함 (실제 임베딩)
    assert sum(abs(x) for x in embedding) > 0


def test_batch_embedding(embedding_service):
    """TC03: 배치 임베딩 생성"""
    texts = [
        "First sentence.",
        "Second sentence.",
        "Third sentence."
    ]

    embeddings = embedding_service.embed_batch(texts)

    assert len(embeddings) == 3
    assert all(len(emb) == 768 for emb in embeddings)
    assert all(sum(abs(x) for x in emb) > 0 for emb in embeddings)


def test_embedding_dimension(embedding_service):
    """TC04: 임베딩 차원 확인"""
    dimension = embedding_service.get_embedding_dimension()

    assert dimension == 768


# ============================================================================
# Edge Case Tests
# ============================================================================

def test_empty_text_embedding(embedding_service):
    """TC05: 빈 텍스트 처리 (0 벡터 반환)"""
    embedding = embedding_service.embed_text("")

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    # 빈 텍스트는 0 벡터 반환
    assert all(x == 0.0 for x in embedding)


def test_whitespace_only_text(embedding_service):
    """TC06: 공백만 있는 텍스트 처리"""
    embedding = embedding_service.embed_text("   ")

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    # 공백만 있는 텍스트도 0 벡터 반환
    assert all(x == 0.0 for x in embedding)


def test_very_long_text(embedding_service):
    """TC07: 매우 긴 텍스트 처리 (2000자)"""
    long_text = "This is a long sentence. " * 100  # 약 2500자

    embedding = embedding_service.embed_text(long_text)

    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert sum(abs(x) for x in embedding) > 0


def test_batch_with_empty_list(embedding_service):
    """TC08: 빈 리스트 배치 처리"""
    embeddings = embedding_service.embed_batch([])

    assert embeddings == []


def test_batch_partial_failure_handling(embedding_service):
    """TC09: 배치 중 일부 실패 처리 (견고성 확인)"""
    # 정상 텍스트와 빈 텍스트 혼합
    texts = [
        "Valid text 1",
        "",  # 빈 텍스트 (0 벡터 반환)
        "Valid text 2"
    ]

    embeddings = embedding_service.embed_batch(texts)

    assert len(embeddings) == 3
    # 첫 번째와 세 번째는 정상 임베딩
    assert sum(abs(x) for x in embeddings[0]) > 0
    assert sum(abs(x) for x in embeddings[2]) > 0
    # 두 번째는 0 벡터
    assert all(x == 0.0 for x in embeddings[1])


# ============================================================================
# Configuration Tests
# ============================================================================

def test_custom_config():
    """TC10: 커스텀 설정으로 서비스 생성"""
    config = EmbeddingConfig(
        model_name="nomic-embed-text",
        expected_dimension=768,
        batch_size=10,
        max_retries=5
    )

    service = OllamaEmbeddingService(config=config)

    assert service.config.batch_size == 10
    assert service.config.max_retries == 5


# ============================================================================
# Integration Tests
# ============================================================================

def test_embedding_consistency(embedding_service):
    """TC11: 동일 텍스트의 임베딩 일관성 검증"""
    text = "This is a consistency test."

    embedding1 = embedding_service.embed_text(text)
    embedding2 = embedding_service.embed_text(text)

    # 동일한 텍스트는 동일한 임베딩을 생성해야 함
    assert embedding1 == embedding2


def test_different_texts_different_embeddings(embedding_service):
    """TC12: 다른 텍스트는 다른 임베딩 생성"""
    text1 = "This is the first sentence."
    text2 = "This is the second sentence."

    embedding1 = embedding_service.embed_text(text1)
    embedding2 = embedding_service.embed_text(text2)

    # 다른 텍스트는 다른 임베딩을 생성해야 함
    assert embedding1 != embedding2
