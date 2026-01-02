"""
Create Milvus collection for RAG document chunks.

Run this script once to initialize the collection:
    python backend/scripts/create_milvus_collection.py
"""

from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)
import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

load_dotenv()


def create_collection():
    """Create RAG document chunks collection with HNSW index."""

    # Connection parameters
    host = os.getenv("MILVUS_HOST", "localhost")
    port = os.getenv("MILVUS_PORT", "19530")
    collection_name = os.getenv("MILVUS_COLLECTION_NAME", "rag_document_chunks")

    print(f"Connecting to Milvus at {host}:{port}...")
    connections.connect(
        alias="default",
        host=host,
        port=port,
        timeout=10
    )

    # Check if collection already exists
    if utility.has_collection(collection_name):
        print(f"⚠️  Collection '{collection_name}' already exists")
        response = input("Drop and recreate? (yes/no): ")
        if response.lower() == "yes":
            utility.drop_collection(collection_name)
            print(f"Dropped existing collection '{collection_name}'")
        else:
            print("Aborting. Collection not modified.")
            return

    # Define schema
    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True,
            description="Auto-generated chunk ID"
        ),
        FieldSchema(
            name="document_id",
            dtype=DataType.VARCHAR,
            max_length=36,
            description="Reference to documents table (UUID)"
        ),
        FieldSchema(
            name="content",
            dtype=DataType.VARCHAR,
            max_length=2000,
            description="Text content of the chunk"
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=768,
            description="Text embedding vector (768-dimensional)"
        ),
        FieldSchema(
            name="chunk_index",
            dtype=DataType.INT32,
            description="Index of chunk within document"
        ),
        FieldSchema(
            name="metadata",
            dtype=DataType.JSON,
            description="Additional metadata (page_number, section, etc.)"
        ),
    ]

    schema = CollectionSchema(
        fields=fields,
        enable_dynamic_field=True,
        description="RAG document chunks with embeddings for semantic search"
    )

    print(f"Creating collection '{collection_name}'...")
    collection = Collection(
        name=collection_name,
        schema=schema,
        using="default"
    )

    # Create HNSW index
    print("Creating HNSW index on 'embedding' field...")
    index_params = {
        "index_type": "HNSW",
        "metric_type": "COSINE",
        "params": {
            "M": 16,
            "efConstruction": 256
        }
    }

    collection.create_index(
        field_name="embedding",
        index_params=index_params,
        index_name="embedding_hnsw_index"
    )

    print("Loading collection into memory...")
    collection.load()

    # Verify creation
    print("\n✅ Collection created successfully!")
    print(f"   Name: {collection.name}")
    print(f"   Schema: {len(collection.schema.fields)} fields")
    print(f"   Index: HNSW (M=16, efConstruction=256)")
    print(f"   Metric: COSINE")
    print(f"   Dimension: 768")
    print(f"   Entities: {collection.num_entities}")

    # Show schema
    print("\n📋 Schema Details:")
    for field in collection.schema.fields:
        print(f"   - {field.name} ({field.dtype})")

    connections.disconnect("default")
    print("\nDisconnected from Milvus")


if __name__ == "__main__":
    try:
        create_collection()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
