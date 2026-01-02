"""
Test Milvus operations with dummy data.

Inserts 5 dummy vectors and performs similarity search.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.milvus_client import milvus_client
import numpy as np
import uuid


def generate_dummy_embedding(seed: int) -> list:
    """Generate dummy 768-dimensional embedding."""
    np.random.seed(seed)
    vector = np.random.rand(768).astype(np.float32)
    # Normalize for COSINE metric
    vector = vector / np.linalg.norm(vector)
    return vector.tolist()


def insert_dummy_data():
    """Insert 5 dummy document chunks."""
    print("Connecting to Milvus...")
    milvus_client.connect()

    # Prepare dummy data
    document_ids = [str(uuid.uuid4()) for _ in range(5)]
    contents = [
        "연차 사용 시 3일 전에 신청해야 합니다.",
        "회사 정책에 따라 연차는 1년에 15일 제공됩니다.",
        "재택근무는 주 2회까지 가능합니다.",
        "출장 신청은 최소 1주일 전에 해야 합니다.",
        "보안 정책상 외부 기기 연결 시 승인이 필요합니다."
    ]
    embeddings = [generate_dummy_embedding(i) for i in range(5)]
    chunk_indices = [0, 1, 2, 3, 4]
    metadata_list = [
        {"page_number": 1, "section": "휴가 정책"},
        {"page_number": 1, "section": "휴가 정책"},
        {"page_number": 2, "section": "근무 방식"},
        {"page_number": 3, "section": "출장 정책"},
        {"page_number": 5, "section": "보안 정책"}
    ]

    # Insert data
    print("Inserting 5 dummy chunks...")
    data = [
        document_ids,
        contents,
        embeddings,
        chunk_indices,
        metadata_list
    ]

    result = milvus_client.insert(data)

    if result["success"]:
        print(f"✅ Inserted {result['insert_count']} chunks")
        print(f"   Primary Keys: {result['primary_keys'][:3]}... (showing first 3)")
    else:
        print(f"❌ Insert failed: {result['error']}")
        return

    # Perform similarity search
    print("\nPerforming similarity search...")
    query_vector = generate_dummy_embedding(0)  # Similar to first chunk

    results = milvus_client.search(
        query_vectors=[query_vector],
        top_k=3,
        output_fields=["document_id", "content", "chunk_index", "metadata"]
    )

    print(f"\n🔍 Search Results (Top 3):")
    for i, hits in enumerate(results):
        for j, hit in enumerate(hits):
            print(f"\n   Rank {j+1}:")
            print(f"   - Distance: {hit.distance:.4f}")
            print(f"   - Content: {hit.entity.get('content')[:50]}...")
            print(f"   - Chunk Index: {hit.entity.get('chunk_index')}")
            print(f"   - Metadata: {hit.entity.get('metadata')}")

    milvus_client.disconnect()
    print("\nDisconnected from Milvus")


if __name__ == "__main__":
    try:
        insert_dummy_data()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
