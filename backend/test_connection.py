#!/usr/bin/env python3
"""
Simple Milvus connection test script.
Tests connectivity without requiring full app initialization.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Milvus Connection Test")
print("=" * 60)

# Show configuration
milvus_host = os.getenv("MILVUS_HOST", "localhost")
milvus_port = os.getenv("MILVUS_PORT", "19530")
print(f"\nConfiguration:")
print(f"  MILVUS_HOST: {milvus_host}")
print(f"  MILVUS_PORT: {milvus_port}")

# Test connection
print(f"\nAttempting to connect to {milvus_host}:{milvus_port}...")

try:
    from pymilvus import connections, utility

    # Connect
    connections.connect(
        alias="test",
        host=milvus_host,
        port=milvus_port,
        timeout=10
    )

    print("✅ Connection successful!")

    # List collections (using the connection alias)
    collections = utility.list_collections(using="test")
    print(f"\n📋 Available collections: {collections}")

    # Check specific collection
    collection_name = os.getenv("MILVUS_COLLECTION_NAME", "rag_document_chunks")
    if collection_name in collections:
        print(f"✅ Collection '{collection_name}' exists")
    else:
        print(f"⚠️  Collection '{collection_name}' not found")
        print(f"   Run: python backend/scripts/create_milvus_collection.py")

    # Disconnect
    connections.disconnect("test")
    print("\n✅ Test completed successfully!")

except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\nPlease install required packages:")
    print("  pip install pymilvus python-dotenv")
    sys.exit(1)

except Exception as e:
    print(f"\n❌ Connection failed: {type(e).__name__}: {e}")
    print("\n🔧 Troubleshooting:")
    print("  1. Check if Milvus is running:")
    print("     docker ps | grep milvus")
    print("  2. Check if port 19530 is accessible:")
    print("     nc -zv localhost 19530")
    print("  3. Check Milvus logs:")
    print("     docker logs rag-milvus --tail 50")
    sys.exit(1)
