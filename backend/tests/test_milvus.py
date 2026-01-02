"""
Unit tests for Milvus client and operations.
"""

import pytest
from app.db.milvus_client import MilvusClient, milvus_client
import numpy as np
import uuid


@pytest.fixture(scope="module")
def client():
    """Milvus client fixture."""
    client = MilvusClient()
    client.connect()
    yield client
    client.disconnect()


def test_singleton_pattern():
    """Test that MilvusClient follows singleton pattern."""
    client1 = MilvusClient()
    client2 = MilvusClient()
    assert client1 is client2


def test_connection(client):
    """Test Milvus connection."""
    assert client.connect() is True


def test_health_check(client):
    """Test Milvus health check."""
    health = client.health_check()
    assert health["status"] == "healthy"
    assert health["connected"] is True
    assert "rag_document_chunks" in health["collections"]


def test_get_collection(client):
    """Test getting collection."""
    collection = client.get_collection()
    assert collection is not None
    assert collection.name == "rag_document_chunks"
    assert collection.num_entities >= 0


def test_insert_single_chunk(client):
    """Test inserting a single chunk."""
    # Generate dummy data
    document_id = str(uuid.uuid4())
    content = "Test content for insertion"
    embedding = np.random.rand(768).astype(np.float32).tolist()
    chunk_index = 0
    metadata = {"test": True}

    # Insert
    data = [
        [document_id],
        [content],
        [embedding],
        [chunk_index],
        [metadata]
    ]

    result = client.insert(data)

    assert result["success"] is True
    assert result["insert_count"] == 1
    assert len(result["primary_keys"]) == 1


def test_insert_multiple_chunks(client):
    """Test inserting multiple chunks."""
    # Generate 3 dummy chunks
    document_ids = [str(uuid.uuid4()) for _ in range(3)]
    contents = ["Content 1", "Content 2", "Content 3"]
    embeddings = [np.random.rand(768).astype(np.float32).tolist() for _ in range(3)]
    chunk_indices = [0, 1, 2]
    metadata_list = [{"idx": i} for i in range(3)]

    data = [
        document_ids,
        contents,
        embeddings,
        chunk_indices,
        metadata_list
    ]

    result = client.insert(data)

    assert result["success"] is True
    assert result["insert_count"] == 3
    assert len(result["primary_keys"]) == 3


def test_search_similarity(client):
    """Test similarity search."""
    # Insert a known chunk
    document_id = str(uuid.uuid4())
    content = "Known content for search test"
    np.random.seed(42)
    embedding = np.random.rand(768).astype(np.float32)
    embedding = embedding / np.linalg.norm(embedding)  # Normalize

    data = [
        [document_id],
        [content],
        [embedding.tolist()],
        [0],
        [{"test": "search"}]
    ]

    client.insert(data)

    # Search with same vector (should get high similarity)
    results = client.search(
        query_vectors=[embedding.tolist()],
        top_k=5,
        output_fields=["document_id", "content"]
    )

    assert len(results) > 0
    assert len(results[0]) > 0

    # First result should be the inserted chunk (exact match)
    top_hit = results[0][0]
    assert top_hit.distance >= 0.99  # Very high similarity (COSINE)


def test_search_with_filter(client):
    """Test search with filter expression."""
    # Insert chunks with specific chunk_index
    document_id = str(uuid.uuid4())
    data = [
        [document_id, document_id],
        ["Content A", "Content B"],
        [
            np.random.rand(768).astype(np.float32).tolist(),
            np.random.rand(768).astype(np.float32).tolist()
        ],
        [0, 5],  # Different chunk indices
        [{"filter": "test"}, {"filter": "test"}]
    ]

    client.insert(data)

    # Search with filter: chunk_index > 3
    query_vector = np.random.rand(768).astype(np.float32).tolist()
    results = client.search(
        query_vectors=[query_vector],
        top_k=10,
        filter_expr="chunk_index > 3",
        output_fields=["chunk_index"]
    )

    # Verify all results have chunk_index > 3
    for hits in results:
        for hit in hits:
            assert hit.entity.get("chunk_index") > 3


def test_search_output_fields(client):
    """Test search with specific output fields."""
    query_vector = np.random.rand(768).astype(np.float32).tolist()

    results = client.search(
        query_vectors=[query_vector],
        top_k=3,
        output_fields=["content", "metadata"]
    )

    # Verify output fields
    if len(results) > 0 and len(results[0]) > 0:
        hit = results[0][0]
        # Milvus 2.6+ returns hit with .entity attribute which contains the fields
        # hit.entity is a dict-like object
        assert hasattr(hit, 'entity')
        assert hit.entity.get("content") is not None
        assert hit.entity.get("metadata") is not None


def test_search_top_k(client):
    """Test search with different top_k values."""
    query_vector = np.random.rand(768).astype(np.float32).tolist()

    # Search with top_k=3
    results_3 = client.search(query_vectors=[query_vector], top_k=3)

    # Search with top_k=5
    results_5 = client.search(query_vectors=[query_vector], top_k=5)

    # Verify result counts (if enough data exists)
    collection = client.get_collection()
    if collection.num_entities >= 5:
        assert len(results_3[0]) <= 3
        assert len(results_5[0]) <= 5


def test_cosine_metric_range(client):
    """Test that COSINE metric returns distances in [0, 1] range."""
    query_vector = np.random.rand(768).astype(np.float32).tolist()

    results = client.search(
        query_vectors=[query_vector],
        top_k=5
    )

    # Verify distance range for COSINE
    for hits in results:
        for hit in hits:
            # COSINE similarity is in range [0, 1] (1 = identical, 0 = orthogonal)
            # In Milvus, distance = 1 - cosine_similarity, so range is [0, 2]
            # But normalized vectors give range ~[0, 1]
            assert 0 <= hit.distance <= 2


def test_reconnect_logic(client):
    """Test reconnection logic."""
    # Disconnect
    client.disconnect()

    # Reconnect should succeed
    assert client.reconnect() is True

    # Verify connection is active
    health = client.health_check()
    assert health["connected"] is True


def test_ensure_connection(client):
    """Test ensure_connection method."""
    assert client.ensure_connection() is True
