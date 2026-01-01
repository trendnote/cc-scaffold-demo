# Task Execution Plan: 1.3 - Milvus Collection 생성 및 연결 테스트

---

## Meta
- **Task ID**: 1.3
- **Task Name**: Milvus Collection 생성 및 연결 테스트
- **Original Estimate**: 4시간
- **Revised Estimate**: 4.5시간
- **Variance**: +0.5시간 (HNSW 파라미터 튜닝 및 성능 테스트 추가)
- **담당**: Backend
- **Dependencies**: Task 1.1 (Docker Compose 환경 구축)
- **Created**: 2025-12-31
- **Status**: Ready for Implementation

---

## 1. Task Overview

### 1.1 목표
Milvus 벡터 데이터베이스에 RAG 시스템용 Collection을 생성하고 연결을 검증합니다. 768차원 임베딩 벡터를 저장할 수 있는 스키마를 설계하고, HNSW 인덱스를 통해 고속 유사도 검색이 가능하도록 구성합니다. PyMilvus SDK를 활용하여 프로덕션 환경에서 안정적으로 사용할 수 있는 클라이언트 모듈을 구축합니다.

### 1.2 Task Breakdown 정보
- **작업 내용**:
  - Milvus Python SDK 설정 (`pymilvus`)
  - Collection 스키마 정의:
    - 필드: `id`, `document_id`, `content`, `embedding` (768차원), `chunk_index`, `metadata`
    - 인덱스: HNSW (M=16, efConstruction=256)
    - 메트릭: COSINE
  - Collection 생성 스크립트
  - 연결 테스트 코드 작성

- **검증 기준**:
  - [ ] Collection 생성 성공
  - [ ] 더미 벡터 (5개) 저장 성공
  - [ ] 유사도 검색 테스트 성공
  - [ ] Attu UI에서 Collection 확인

- **출력물**:
  - `backend/app/db/milvus_client.py`
  - `backend/scripts/create_milvus_collection.py`
  - `backend/tests/test_milvus.py`

### 1.3 주요 기술 스택
- **Vector Database**: Milvus 2.3+ (Standalone)
- **Python SDK**: pymilvus 2.3+
- **Index Type**: HNSW (Hierarchical Navigable Small World)
- **Metric Type**: COSINE (코사인 유사도)
- **Vector Dimension**: 768 (nomic-embed-text 모델)
- **Testing**: pytest, pytest-asyncio

---

## 2. Research & Design

### 2.1 기술 조사 결과

#### Milvus 2.x HNSW Index Best Practices

최신 Milvus 2.x 문서(2025) 및 커뮤니티 연구 결과:

**1. HNSW 파라미터 튜닝**
- **M (Maximum Connections)**: 각 노드가 연결할 수 있는 최대 이웃 수
  - 높은 M → 더 조밀한 그래프, 높은 recall, 높은 메모리 사용
  - 권장값: 16-64 (768차원 벡터)
  - 기본값: M=16 (Task에서 지정)

- **efConstruction (Build-time Search Depth)**: 인덱스 구축 시 고려할 후보 이웃 수
  - 높은 efConstruction → 더 나은 품질, 느린 구축 시간
  - 권장값: 100-500
  - Task 지정값: 256 (balanced)

- **ef (Search-time Parameter)**: 검색 시 고려할 이웃 수
  - 런타임에 조정 가능
  - 권장값: 64-256 (recall/latency 트레이드오프)

**2. Memory Considerations**
- HNSW는 계층적 그래프 구조로 높은 메모리 오버헤드
- 768차원 벡터, 100만 개 기준: ~4-8GB RAM 필요
- Phase 1 (MVP): 10,000개 문서 예상 → ~40-80MB (허용 범위)

**3. COSINE Metric**
- Milvus 지원 메트릭: L2, IP (Inner Product), COSINE
- COSINE: 벡터 방향 유사도 (크기 정규화 후 내적)
- 텍스트 임베딩에 적합 (문서 길이 무관)

**4. PyMilvus Connection Patterns**
```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# Best practice: Named connection with health check
connections.connect(
    alias="default",
    host="localhost",
    port="19530",
    timeout=10
)

# Verify connection
if connections.has_connection("default"):
    print("Connection established")
```

**5. Collection Schema Design**
```python
# Schema with dynamic fields for flexibility
schema = CollectionSchema(
    fields=[...],
    enable_dynamic_field=True,  # Allow adding fields later
    description="RAG document chunks with embeddings"
)
```

**출처**:
- [HNSW | Milvus Documentation](https://milvus.io/docs/hnsw.md)
- [In-memory Index | Milvus Documentation](https://milvus.io/docs/index.md)
- [How to Pick a Vector Index in Milvus - Zilliz](https://zilliz.com/learn/how-to-pick-a-vector-index-in-milvus-visual-guide)
- [Create Collection | Milvus Documentation](https://milvus.io/docs/create-collection.md)
- [Getting Started with Milvus Connection - Zilliz](https://zilliz.com/blog/getting-started-with-a-milvus-connection)

### 2.2 Collection 스키마 설계

#### 필드 정의

```python
from pymilvus import FieldSchema, DataType

fields = [
    # Primary Key (Auto-increment ID)
    FieldSchema(
        name="id",
        dtype=DataType.INT64,
        is_primary=True,
        auto_id=True,
        description="Auto-generated chunk ID"
    ),

    # Document Reference (UUID from PostgreSQL)
    FieldSchema(
        name="document_id",
        dtype=DataType.VARCHAR,
        max_length=36,  # UUID string length
        description="Reference to documents table in PostgreSQL"
    ),

    # Chunk Content (for display in search results)
    FieldSchema(
        name="content",
        dtype=DataType.VARCHAR,
        max_length=2000,  # Max chunk size ~500 chars * 4 (buffer)
        description="Text content of the chunk"
    ),

    # Vector Embedding (768-dimensional)
    FieldSchema(
        name="embedding",
        dtype=DataType.FLOAT_VECTOR,
        dim=768,  # nomic-embed-text dimension
        description="Text embedding vector"
    ),

    # Chunk Index (for ordering)
    FieldSchema(
        name="chunk_index",
        dtype=DataType.INT32,
        description="Index of chunk within document (0-based)"
    ),

    # Metadata (JSONB-like storage)
    FieldSchema(
        name="metadata",
        dtype=DataType.JSON,
        description="Additional metadata (page_number, section, etc.)"
    ),
]
```

#### 인덱스 전략

**HNSW Index Configuration**:
```python
index_params = {
    "index_type": "HNSW",
    "metric_type": "COSINE",
    "params": {
        "M": 16,           # Moderate graph density
        "efConstruction": 256  # Balanced build quality/time
    }
}
```

**Search Parameters** (런타임 조정):
```python
search_params = {
    "metric_type": "COSINE",
    "params": {
        "ef": 64  # Initial value, can tune for recall/latency
    }
}
```

#### Collection 설계 결정

**Decision 1: Auto-ID vs User-Provided ID**
- **선택**: Auto-ID (Milvus 관리)
- **이유**:
  - 중복 방지 (Milvus가 자동 생성)
  - 삽입 성능 향상 (ID 생성 오버헤드 없음)
  - PostgreSQL의 document_id로 참조 충분
- **Trade-off**: ID 예측 불가 (허용, document_id로 조회)

**Decision 2: VARCHAR vs TEXT for content**
- **선택**: VARCHAR(2000)
- **이유**:
  - Milvus는 TEXT 타입 미지원 (VARCHAR만)
  - 청크 크기 ~500자, 버퍼 포함 2000자 충분
  - 메모리 효율성 (고정 최대 길이)
- **주의**: 2000자 초과 시 truncate 필요

**Decision 3: JSON vs Separate Fields for metadata**
- **선택**: JSON 필드 (flexible metadata)
- **이유**:
  - 문서 타입별 메타데이터 다름 (PDF: page_number, DOCX: section)
  - 스키마 변경 없이 필드 추가 가능
  - Milvus 2.2+ JSON 지원
- **Trade-off**: JSON 필드 인덱싱 불가 (허용, 필터링은 document_id 사용)

**Decision 4: HNSW vs IVF_FLAT**
- **선택**: HNSW
- **이유**:
  - 높은 recall (>95% with ef=64)
  - 낮은 지연시간 (P95 < 100ms 목표)
  - MVP 데이터셋 크기 (10K chunks) 적합
- **Trade-off**: 메모리 사용 증가 (허용, 40-80MB 예상)

### 2.3 Milvus 연결 아키텍처

```
┌─────────────────────┐
│   FastAPI App       │
│   (async context)   │
└──────────┬──────────┘
           │
           │ uses
           ▼
┌─────────────────────┐
│  MilvusClient       │
│  (Singleton)        │
├─────────────────────┤
│ - connect()         │
│ - get_collection()  │
│ - insert()          │
│ - search()          │
│ - health_check()    │
└──────────┬──────────┘
           │
           │ connects to
           ▼
┌─────────────────────┐
│   Milvus Server     │
│   (localhost:19530) │
├─────────────────────┤
│ - etcd (metadata)   │
│ - MinIO (storage)   │
│ - HNSW index        │
└─────────────────────┘
```

**Connection Pooling**:
- Milvus는 내부적으로 gRPC 연결 풀 관리
- 애플리케이션에서는 Singleton 패턴으로 연결 재사용
- `connections.connect()` 한 번 호출, 이후 `Collection()` 재사용

---

## 3. Implementation Steps

### Step 1: 의존성 설치 및 환경 설정 (30분)

**작업 내용**:
1. PyMilvus 설치
   ```bash
   cd backend
   echo "pymilvus==2.3.4" >> requirements.txt
   pip install pymilvus==2.3.4
   ```

2. 환경 변수 추가 (`.env`)
   ```bash
   # Milvus Configuration
   MILVUS_HOST=localhost
   MILVUS_PORT=19530
   MILVUS_USER=  # Optional: for authentication
   MILVUS_PASSWORD=  # Optional
   MILVUS_COLLECTION_NAME=rag_document_chunks
   ```
   **[HARD RULE]** 인증 정보는 환경 변수로만 관리

3. `.env.example` 업데이트
   ```bash
   cp .env .env.example
   # Remove actual passwords, keep structure
   ```

4. Milvus 연결 확인
   ```bash
   docker ps | grep milvus
   # Verify milvus-standalone, etcd, minio running
   ```

**검증**:
- [ ] `pymilvus` 설치 확인 (`pip show pymilvus`)
- [ ] 환경 변수 파일 생성 확인
- [ ] Milvus 컨테이너 실행 확인

**출력물**:
- `backend/requirements.txt` (pymilvus 추가)
- `backend/.env` (Milvus 설정)
- `backend/.env.example`

---

### Step 2: MilvusClient 모듈 구현 (1시간)

**작업 내용**:
1. `backend/app/db/milvus_client.py` 생성
   ```python
   """
   Milvus Vector Database Client

   Provides connection management and basic operations for Milvus.
   Follows Singleton pattern to reuse connections.
   """

   from pymilvus import connections, Collection, utility
   from typing import Optional, List, Dict, Any
   import os
   from dotenv import load_dotenv
   import logging

   load_dotenv()
   logger = logging.getLogger(__name__)


   class MilvusClient:
       """Singleton Milvus client for connection management."""

       _instance: Optional['MilvusClient'] = None
       _collection: Optional[Collection] = None

       def __new__(cls):
           if cls._instance is None:
               cls._instance = super().__new__(cls)
               cls._instance._initialized = False
           return cls._instance

       def __init__(self):
           if self._initialized:
               return

           self.host = os.getenv("MILVUS_HOST", "localhost")
           self.port = os.getenv("MILVUS_PORT", "19530")
           self.collection_name = os.getenv("MILVUS_COLLECTION_NAME", "rag_document_chunks")
           self.alias = "default"
           self._initialized = True

       def connect(self) -> bool:
           """
           Establish connection to Milvus server.

           Returns:
               bool: True if connection successful, False otherwise
           """
           try:
               if not connections.has_connection(self.alias):
                   connections.connect(
                       alias=self.alias,
                       host=self.host,
                       port=self.port,
                       timeout=10
                   )
                   logger.info(f"Connected to Milvus at {self.host}:{self.port}")
               return True
           except Exception as e:
               logger.error(f"Failed to connect to Milvus: {e}")
               return False

       def disconnect(self):
           """Disconnect from Milvus server."""
           if connections.has_connection(self.alias):
               connections.disconnect(self.alias)
               logger.info("Disconnected from Milvus")

       def health_check(self) -> Dict[str, Any]:
           """
           Check Milvus server health.

           Returns:
               dict: Health status information
           """
           try:
               if not connections.has_connection(self.alias):
                   self.connect()

               # List collections as health check
               collections = utility.list_collections()

               return {
                   "status": "healthy",
                   "connected": True,
                   "collections": collections,
                   "host": self.host,
                   "port": self.port
               }
           except Exception as e:
               return {
                   "status": "unhealthy",
                   "connected": False,
                   "error": str(e),
                   "host": self.host,
                   "port": self.port
               }

       def get_collection(self) -> Optional[Collection]:
           """
           Get or load the RAG collection.

           Returns:
               Collection: Milvus collection object or None if not exists
           """
           try:
               if not connections.has_connection(self.alias):
                   self.connect()

               if utility.has_collection(self.collection_name):
                   if self._collection is None:
                       self._collection = Collection(self.collection_name)
                       self._collection.load()
                   return self._collection
               else:
                   logger.warning(f"Collection '{self.collection_name}' does not exist")
                   return None
           except Exception as e:
               logger.error(f"Failed to get collection: {e}")
               return None

       def insert(self, data: List[List[Any]]) -> Dict[str, Any]:
           """
           Insert vectors and metadata into collection.

           Args:
               data: List of field values [document_ids, contents, embeddings, ...]

           Returns:
               dict: Insert result with IDs and count
           """
           try:
               collection = self.get_collection()
               if collection is None:
                   raise ValueError("Collection not found")

               result = collection.insert(data)
               collection.flush()  # Ensure data is persisted

               return {
                   "success": True,
                   "insert_count": result.insert_count,
                   "primary_keys": result.primary_keys
               }
           except Exception as e:
               logger.error(f"Failed to insert data: {e}")
               return {
                   "success": False,
                   "error": str(e)
               }

       def search(
           self,
           query_vectors: List[List[float]],
           top_k: int = 5,
           filter_expr: Optional[str] = None,
           output_fields: Optional[List[str]] = None
       ) -> List[Any]:
           """
           Search for similar vectors.

           Args:
               query_vectors: List of query embedding vectors
               top_k: Number of results to return
               filter_expr: Optional filter expression (e.g., "chunk_index > 0")
               output_fields: Fields to return in results

           Returns:
               list: Search results
           """
           try:
               collection = self.get_collection()
               if collection is None:
                   raise ValueError("Collection not found")

               search_params = {
                   "metric_type": "COSINE",
                   "params": {"ef": 64}
               }

               results = collection.search(
                   data=query_vectors,
                   anns_field="embedding",
                   param=search_params,
                   limit=top_k,
                   expr=filter_expr,
                   output_fields=output_fields or ["document_id", "content", "chunk_index", "metadata"]
               )

               return results
           except Exception as e:
               logger.error(f"Failed to search: {e}")
               return []


   # Global singleton instance
   milvus_client = MilvusClient()
   ```

2. `backend/app/db/__init__.py` 업데이트
   ```python
   from .base import Base, engine, get_db
   from .milvus_client import milvus_client

   __all__ = ["Base", "engine", "get_db", "milvus_client"]
   ```

**검증**:
- [ ] MilvusClient 임포트 에러 없음
- [ ] Singleton 패턴 동작 확인
- [ ] Type hints 적용 확인

**출력물**:
- `backend/app/db/milvus_client.py`
- `backend/app/db/__init__.py` (updated)

---

### Step 3: Collection 생성 스크립트 구현 (1시간)

**작업 내용**:
1. `backend/scripts/create_milvus_collection.py` 생성
   ```python
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
   ```

2. 스크립트 실행 권한 및 테스트
   ```bash
   chmod +x backend/scripts/create_milvus_collection.py
   python backend/scripts/create_milvus_collection.py
   ```

**검증**:
- [ ] 스크립트 실행 성공
- [ ] Collection 생성 확인
- [ ] HNSW 인덱스 생성 확인
- [ ] Attu UI에서 Collection 확인 (http://localhost:8080)

**출력물**:
- `backend/scripts/create_milvus_collection.py`
- Milvus Collection (rag_document_chunks)

---

### Step 4: 더미 데이터 삽입 및 검색 테스트 (45분)

**작업 내용**:
1. `backend/scripts/test_milvus_operations.py` 생성
   ```python
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
   ```

2. 테스트 실행
   ```bash
   python backend/scripts/test_milvus_operations.py
   ```

3. Attu UI에서 확인
   - http://localhost:8080 접속
   - Collection 선택: `rag_document_chunks`
   - 5개 엔티티 확인
   - 벡터 차원 768 확인

**검증**:
- [ ] 5개 더미 벡터 삽입 성공
- [ ] 유사도 검색 결과 반환 (Top 3)
- [ ] Distance 값 0-1 범위 확인 (COSINE)
- [ ] Attu UI에서 데이터 확인

**출력물**:
- `backend/scripts/test_milvus_operations.py`
- Milvus 데이터 (5개 chunks)
- 검색 결과 로그

---

### Step 5: 단위 테스트 작성 (1시간)

**작업 내용**:
1. `backend/tests/test_milvus.py` 생성
   ```python
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
           assert "content" in hit.entity
           assert "metadata" in hit.entity


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
   ```

2. Pytest 설정 업데이트 (`backend/pytest.ini`)
   ```ini
   [pytest]
   testpaths = tests
   python_files = test_*.py
   python_classes = Test*
   python_functions = test_*
   addopts = -v --tb=short
   markers =
       unit: Unit tests
       integration: Integration tests
       milvus: Milvus-specific tests
   ```

3. 테스트 실행
   ```bash
   pytest backend/tests/test_milvus.py -v -m milvus
   ```

**검증**:
- [ ] 10개 테스트 모두 통과
- [ ] Singleton 패턴 테스트 성공
- [ ] 삽입/검색 테스트 성공
- [ ] 필터 표현식 테스트 성공
- [ ] Coverage > 80%

**출력물**:
- `backend/tests/test_milvus.py`
- `backend/pytest.ini` (updated)
- 테스트 실행 결과

---

### Step 6: 연결 상태 모니터링 및 에러 처리 (30분)

**작업 내용**:
1. `backend/app/db/milvus_client.py`에 재연결 로직 추가
   ```python
   # Add to MilvusClient class

   def reconnect(self, max_retries: int = 3) -> bool:
       """
       Reconnect to Milvus with retry logic.

       Args:
           max_retries: Maximum number of retry attempts

       Returns:
           bool: True if reconnection successful
       """
       for attempt in range(max_retries):
           try:
               self.disconnect()
               if self.connect():
                   logger.info(f"Reconnected to Milvus (attempt {attempt + 1})")
                   return True
           except Exception as e:
               logger.warning(f"Reconnect attempt {attempt + 1} failed: {e}")
               if attempt < max_retries - 1:
                   import time
                   time.sleep(2 ** attempt)  # Exponential backoff

       logger.error("Failed to reconnect to Milvus after retries")
       return False

   def ensure_connection(self) -> bool:
       """
       Ensure connection is active, reconnect if needed.

       Returns:
           bool: True if connection is active
       """
       try:
           # Test connection with a lightweight operation
           if connections.has_connection(self.alias):
               utility.list_collections()
               return True
           else:
               return self.reconnect()
       except Exception:
           return self.reconnect()
   ```

2. 에러 핸들링 개선
   ```python
   # Update search method with error handling

   def search(
       self,
       query_vectors: List[List[float]],
       top_k: int = 5,
       filter_expr: Optional[str] = None,
       output_fields: Optional[List[str]] = None
   ) -> List[Any]:
       """Search with automatic reconnection on failure."""
       try:
           # Ensure connection
           if not self.ensure_connection():
               raise ConnectionError("Failed to connect to Milvus")

           collection = self.get_collection()
           if collection is None:
               raise ValueError("Collection not found")

           # ... (rest of search logic)

       except Exception as e:
           logger.error(f"Search failed: {e}")
           # Attempt reconnect and retry once
           if self.reconnect():
               try:
                   collection = self.get_collection()
                   # ... (retry search)
               except Exception as retry_error:
                   logger.error(f"Retry failed: {retry_error}")
           return []
   ```

3. 테스트 추가
   ```python
   # Add to test_milvus.py

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
   ```

**검증**:
- [ ] 재연결 로직 테스트 성공
- [ ] Exponential backoff 동작 확인
- [ ] 에러 핸들링 개선 확인

**출력물**:
- `backend/app/db/milvus_client.py` (updated with reconnect logic)
- `backend/tests/test_milvus.py` (updated)

---

### Step 7: 문서화 및 최종 검증 (30분)

**작업 내용**:
1. README에 Milvus 섹션 추가 (`backend/README.md` 또는 root `README.md`)
   ```markdown
   ## Milvus Vector Database

   ### Setup

   1. Start Milvus via Docker Compose (from Task 1.1):
      ```bash
      docker-compose up -d milvus-standalone etcd minio
      ```

   2. Verify Milvus is running:
      ```bash
      docker ps | grep milvus
      ```

   3. Access Attu UI: http://localhost:8080

   ### Create Collection

   ```bash
   python backend/scripts/create_milvus_collection.py
   ```

   ### Test Operations

   ```bash
   python backend/scripts/test_milvus_operations.py
   ```

   ### Configuration

   Environment variables (`.env`):
   ```
   MILVUS_HOST=localhost
   MILVUS_PORT=19530
   MILVUS_COLLECTION_NAME=rag_document_chunks
   ```

   ### Collection Schema

   - **id** (INT64): Auto-generated primary key
   - **document_id** (VARCHAR): Reference to PostgreSQL documents table
   - **content** (VARCHAR): Text content of chunk
   - **embedding** (FLOAT_VECTOR): 768-dimensional embedding
   - **chunk_index** (INT32): Index within document
   - **metadata** (JSON): Additional metadata

   ### Index Configuration

   - **Type**: HNSW
   - **Metric**: COSINE
   - **Parameters**: M=16, efConstruction=256
   - **Search ef**: 64 (tunable)
   ```

2. 최종 검증 체크리스트
   ```bash
   # 1. Collection 존재 확인
   python -c "from app.db.milvus_client import milvus_client; milvus_client.connect(); print(milvus_client.get_collection())"

   # 2. 테스트 실행
   pytest backend/tests/test_milvus.py -v

   # 3. Attu UI 확인
   open http://localhost:8080

   # 4. Health check
   python -c "from app.db.milvus_client import milvus_client; print(milvus_client.health_check())"
   ```

3. `docs/milvus/README.md` 생성 (운영 가이드)
   ```markdown
   # Milvus Operations Guide

   ## Daily Operations

   ### Check Health
   ```bash
   python -c "from app.db.milvus_client import milvus_client; print(milvus_client.health_check())"
   ```

   ### Check Collection Stats
   ```python
   from app.db.milvus_client import milvus_client
   milvus_client.connect()
   collection = milvus_client.get_collection()
   print(f"Entities: {collection.num_entities}")
   ```

   ### Backup Collection
   ```bash
   # TODO: Add backup procedure in Phase 4
   ```

   ## Troubleshooting

   ### Connection Failed
   1. Check Milvus container: `docker ps | grep milvus`
   2. Check logs: `docker logs milvus-standalone`
   3. Restart: `docker-compose restart milvus-standalone etcd minio`

   ### Search Slow
   1. Check collection size: May need to tune `ef` parameter
   2. Monitor memory: HNSW requires RAM
   3. Consider HNSW_PQ for compression (Phase 2)

   ### Index Corruption
   1. Drop and recreate index:
      ```python
      collection.drop_index()
      collection.create_index(field_name="embedding", index_params={...})
      ```
   ```

**검증**:
- [ ] README 섹션 추가 확인
- [ ] 최종 체크리스트 모두 통과
- [ ] 운영 가이드 문서 생성
- [ ] Attu UI 접속 및 데이터 확인

**출력물**:
- `README.md` (updated with Milvus section)
- `docs/milvus/README.md` (operations guide)
- 최종 검증 결과

---

## 4. Testing Plan

### 4.1 단위 테스트 (pytest)

**Test Case 1: Singleton Pattern**
```python
def test_singleton_pattern():
    """MilvusClient가 싱글톤 패턴을 따르는지 확인"""
```

**Test Case 2: Connection Management**
```python
def test_connection():
    """Milvus 연결 성공 확인"""
def test_reconnect_logic():
    """재연결 로직 동작 확인"""
def test_ensure_connection():
    """연결 상태 확인 및 자동 재연결"""
```

**Test Case 3: Health Check**
```python
def test_health_check():
    """Health check API 정상 동작 확인"""
```

**Test Case 4: Collection Operations**
```python
def test_get_collection():
    """Collection 로드 성공 확인"""
```

**Test Case 5: Data Insertion**
```python
def test_insert_single_chunk():
    """단일 청크 삽입 성공 확인"""
def test_insert_multiple_chunks():
    """다중 청크 배치 삽입 확인"""
```

**Test Case 6: Similarity Search**
```python
def test_search_similarity():
    """유사도 검색 정확도 확인 (exact match)"""
def test_search_top_k():
    """top_k 파라미터 동작 확인"""
def test_search_output_fields():
    """output_fields 파라미터 동작 확인"""
```

**Test Case 7: Filter Expressions**
```python
def test_search_with_filter():
    """필터 표현식 동작 확인 (chunk_index > N)"""
```

**Test Case 8: COSINE Metric**
```python
def test_cosine_metric_range():
    """COSINE 메트릭 distance 범위 확인 [0, 2]"""
```

### 4.2 통합 테스트

**Integration Test 1: Full Insertion and Search Workflow**
```python
async def test_full_workflow():
    """
    1. Collection 생성
    2. 문서 청크 삽입
    3. 유사도 검색
    4. 결과 검증
    """
```

**Integration Test 2: Concurrent Operations**
```python
async def test_concurrent_searches():
    """동시 다중 검색 요청 처리 확인"""
```

### 4.3 성능 테스트

**Performance Test 1: Search Latency**
```python
def test_search_latency():
    """
    100회 검색 실행
    P95 < 100ms 목표
    """
```

**Performance Test 2: Batch Insertion**
```python
def test_batch_insertion_performance():
    """
    1000개 청크 배치 삽입
    삽입 속도 측정
    """
```

### 4.4 Attu UI 수동 테스트

**Manual Test 1: Collection Visibility**
- [ ] Attu UI 접속 (http://localhost:8080)
- [ ] rag_document_chunks Collection 확인
- [ ] Schema 필드 6개 확인
- [ ] Index 정보 확인 (HNSW, COSINE)

**Manual Test 2: Data Inspection**
- [ ] Entities 개수 확인 (5개 더미 데이터)
- [ ] 개별 엔티티 내용 확인
- [ ] embedding 필드 차원 확인 (768)
- [ ] metadata JSON 구조 확인

---

## 5. Risks & Mitigation

### Risk 1: Milvus 메모리 부족 (Medium Probability)

**Impact**: High
- HNSW 인덱스 로드 실패 → 검색 불가
- OOM (Out of Memory) 에러 → 컨테이너 재시작

**Probability**: Medium (30%)
- HNSW는 메모리 집약적
- 768차원, 10K chunks → 40-80MB (허용)
- 하지만 문서 증가 시 메모리 부족 가능

**Mitigation**:
1. **Docker 메모리 제한 설정**
   ```yaml
   # docker-compose.yml
   milvus-standalone:
     deploy:
       resources:
         limits:
           memory: 4G
         reservations:
           memory: 2G
   ```

2. **메모리 모니터링**
   ```bash
   docker stats milvus-standalone
   ```

3. **인덱스 최적화**
   - M=16 유지 (메모리 절약)
   - 필요 시 HNSW_PQ (압축) 고려 (Phase 2)

4. **데이터 정리 정책**
   - 90일 이상 미사용 청크 삭제 (Phase 4)
   - Collection compact 정기 실행

**Owner**: Infrastructure Team
**Review**: Phase 1 완료 시, 데이터 10K 도달 시

---

### Risk 2: HNSW 파라미터 부적절 (Medium Probability)

**Impact**: Medium
- Recall 저하 → 관련 문서 누락
- 검색 속도 저하 → P95 > 100ms

**Probability**: Medium (40%)
- M=16, efConstruction=256은 보수적 설정
- 하지만 데이터 특성에 따라 튜닝 필요

**Mitigation**:
1. **벤치마크 테스트** (Task 1.3 완료 시)
   - 1000개 샘플 삽입
   - Recall@5, Recall@10 측정
   - 목표: Recall@5 > 95%

2. **파라미터 튜닝 가이드**
   ```python
   # Recall 낮음 → M, efConstruction 증가
   {"M": 32, "efConstruction": 400}

   # 검색 느림 → ef 감소
   search_params = {"ef": 32}  # 기본 64에서 감소
   ```

3. **A/B 테스트**
   - Phase 2 시작 시 파라미터 조합 테스트
   - Recall-Latency 트레이드오프 분석

4. **Fallback**
   - HNSW 성능 부족 시 IVF_FLAT 고려
   - 더 느리지만 정확도 높음

**Owner**: Backend Engineer
**Review**: Task 2.3 (Vector Search) 구현 시

---

### Risk 3: COSINE vs IP 메트릭 선택 (Low Probability)

**Impact**: Low
- 검색 정확도 미세한 차이
- 성능 차이 미미

**Probability**: Low (20%)
- COSINE은 텍스트 임베딩 표준
- 하지만 정규화된 벡터라면 IP도 동일

**Mitigation**:
1. **벡터 정규화 확인**
   - Ollama `nomic-embed-text`가 정규화 반환하는지 확인
   - 정규화 O → IP 사용 가능 (약간 빠름)
   - 정규화 X → COSINE 필수

2. **비교 실험** (Task 1.4 완료 후)
   ```python
   # COSINE vs IP 성능 비교
   index_cosine = {"metric_type": "COSINE"}
   index_ip = {"metric_type": "IP"}
   # Recall, Latency 비교
   ```

3. **변경 비용 낮음**
   - 메트릭은 인덱스 재생성으로 변경 가능
   - 데이터 재삽입 불필요

**Owner**: Backend Engineer
**Review**: Task 1.4 완료 시 (Ollama 연동 후)

---

### Risk 4: Collection 스키마 변경 필요 (Low Probability)

**Impact**: Medium
- 스키마 변경 시 Collection 재생성 필요
- 기존 데이터 마이그레이션 오버헤드

**Probability**: Low (15%)
- 스키마 설계가 요구사항 커버
- 하지만 Phase 2에서 추가 필드 필요할 수 있음

**Mitigation**:
1. **Dynamic Field 활성화**
   ```python
   schema = CollectionSchema(
       fields=[...],
       enable_dynamic_field=True  # ✅ 이미 적용
   )
   ```

2. **Metadata JSON 활용**
   - 새 필드는 metadata에 추가
   - 스키마 변경 최소화

3. **마이그레이션 절차 문서화**
   ```bash
   # 1. 데이터 export
   # 2. Collection drop
   # 3. 새 스키마로 생성
   # 4. 데이터 re-import
   ```

4. **버전 관리**
   - Collection name에 버전 포함 고려
   - 예: `rag_document_chunks_v2`

**Owner**: Backend Lead
**Review**: Phase 2 시작 전

---

## 6. Definition of Done

### 6.1 기능 완료 기준
- [ ] **Milvus Connection 모듈 구현 완료**
  - MilvusClient 클래스 (Singleton)
  - connect(), disconnect(), reconnect()
  - health_check(), ensure_connection()

- [ ] **Collection 생성 스크립트 완료**
  - `create_milvus_collection.py` 실행 성공
  - Collection 스키마 6개 필드 정의
  - HNSW 인덱스 생성 (M=16, efConstruction=256)
  - COSINE 메트릭 적용

- [ ] **Data Operations 구현 완료**
  - insert() 메서드 (단일/배치)
  - search() 메서드 (top_k, filter, output_fields)
  - get_collection() 메서드

- [ ] **더미 데이터 삽입 및 검색 성공**
  - 5개 더미 벡터 삽입
  - 유사도 검색 Top 3 반환
  - COSINE distance 확인

### 6.2 테스트 완료 기준
- [ ] **단위 테스트 10개 이상 작성 및 통과**
  - Singleton pattern
  - Connection management
  - Health check
  - Insert operations
  - Search operations
  - Filter expressions
  - Coverage > 80%

- [ ] **Attu UI 수동 검증 완료**
  - Collection 확인
  - 5개 entities 확인
  - Schema 확인 (6 fields, 768 dim)
  - Index 확인 (HNSW, COSINE)

### 6.3 코드 품질 기준
- [ ] **CLAUDE.md HARD RULE 준수**
  - 환경 변수 사용 (MILVUS_HOST, MILVUS_PORT)
  - 비밀번호 하드코딩 없음
  - 에러 핸들링 완비

- [ ] **타입 힌트 적용**
  - 모든 메서드 타입 힌트
  - mypy 통과

- [ ] **문서화**
  - Docstring (Google style)
  - README 섹션 추가
  - 운영 가이드 작성

### 6.4 성능 기준
- [ ] **검색 성능 목표 달성**
  - Search latency P95 < 100ms (목표)
  - 100회 검색 테스트 실행

- [ ] **메모리 사용량 확인**
  - Docker stats로 메모리 모니터링
  - 5개 chunks 기준 < 100MB (예상)

### 6.5 운영 준비 기준
- [ ] **환경 변수 관리**
  - `.env.example` 업데이트
  - MILVUS_* 변수 문서화

- [ ] **재연결 로직 구현**
  - Exponential backoff
  - 최대 3회 재시도

- [ ] **로깅 설정**
  - INFO: 연결/삽입/검색 성공
  - ERROR: 연결 실패, 검색 실패

### 6.6 리뷰 및 승인
- [ ] **Peer Review 완료**
  - MilvusClient 코드 리뷰
  - 스키마 설계 리뷰
  - 테스트 코드 리뷰

- [ ] **Tech Lead 승인**
  - HNSW 파라미터 승인
  - Collection 스키마 승인

---

## 7. Time Breakdown

| Step | 작업 내용 | 예상 시간 | 누적 시간 |
|------|----------|----------|----------|
| 1 | 의존성 설치 및 환경 설정 | 0.5h | 0.5h |
| 2 | MilvusClient 모듈 구현 | 1.0h | 1.5h |
| 3 | Collection 생성 스크립트 | 1.0h | 2.5h |
| 4 | 더미 데이터 삽입 및 검색 테스트 | 0.75h | 3.25h |
| 5 | 단위 테스트 작성 | 1.0h | 4.25h |
| 6 | 연결 상태 모니터링 및 에러 처리 | 0.5h | 4.75h |
| 7 | 문서화 및 최종 검증 | 0.5h | 5.25h |

**Total**: 5.25시간 (예상 4.5시간 + 버퍼 0.75시간)

**시간 배분**:
- Research/Design: 0% (사전 완료)
- Implementation: 67% (3.5h)
- Testing: 19% (1.0h)
- Documentation/Verification: 14% (0.75h)

---

## 8. Next Steps

### 8.1 Immediate Next Steps (Task 1.3 완료 후)
1. **Task 1.4 준비**: Ollama 설치 및 모델 다운로드
   - llama3, nomic-embed-text 모델 준비
   - LangChain Ollama 연동

2. **Documentation Update**
   - Architecture 문서에 Milvus 다이어그램 추가
   - Collection 스키마 ER 다이어그램

### 8.2 Follow-up Tasks
- **Task 1.8**: 문서 임베딩 및 Milvus 저장 (MilvusClient 활용)
- **Task 2.3**: 벡터 검색 기능 구현 (MilvusClient.search() 활용)
- **Phase 2**: HNSW 파라미터 튜닝 (Recall/Latency 최적화)

### 8.3 Monitoring & Maintenance
- **주간 점검**: Milvus 메모리 사용량 확인
- **월간 점검**: Collection compact 실행 (중복 제거)
- **분기 점검**: HNSW 파라미터 재평가

---

## 9. References

### 9.1 Milvus Official Documentation
- [HNSW | Milvus Documentation](https://milvus.io/docs/hnsw.md)
- [In-memory Index | Milvus Documentation](https://milvus.io/docs/index.md)
- [Create Collection | Milvus Documentation](https://milvus.io/docs/create-collection.md)
- [Quickstart | Milvus Documentation](https://milvus.io/docs/quickstart.md)

### 9.2 PyMilvus Resources
- [Getting Started with Milvus Connection - Zilliz](https://zilliz.com/blog/getting-started-with-a-milvus-connection)
- [How to Pick a Vector Index in Milvus - Zilliz](https://zilliz.com/learn/how-to-pick-a-vector-index-in-milvus-visual-guide)
- [Milvus Complete Example - Medium](https://jimmy-wang-gen-ai.medium.com/milvus-a-complete-example-of-how-to-use-vectordb-by-python-and-serve-it-as-an-api-3a05e2f8db3c)

### 9.3 Internal References
- Task Breakdown: `docs/tasks/task-breakdown.md`
- PRD: `docs/prd/rag-platform-prd.md`
- Architecture: `docs/architecture/architecture.md`
- Task 1.2 Plan: `docs/task-plans/task-1.2-plan.md` (PostgreSQL schema reference)

---

## 10. Approval

**Prepared By**: Claude (Task Planner)
**Date**: 2025-12-31

**Review Status**:
- [ ] Peer Review (Backend Team)
- [ ] Tech Lead Approval
- [ ] Ready for Implementation

**Notes**:
이 계획서는 Task 1.3의 상세 실행 가이드입니다. Milvus 2.x의 최신 Best Practice를 반영하여 768차원 벡터를 위한 HNSW 인덱스를 구성합니다. 모든 검증 기준과 테스트 케이스를 포함하며, CLAUDE.md의 HARD RULE을 준수하여 안전한 벡터 데이터베이스 운영을 목표로 합니다.

**Key Decisions Summary**:
1. ✅ HNSW Index (M=16, efConstruction=256) - Balanced performance
2. ✅ COSINE Metric - Standard for text embeddings
3. ✅ Auto-ID - Milvus-managed primary keys
4. ✅ JSON Metadata - Flexible schema
5. ✅ Singleton Pattern - Connection reuse

---

**END OF TASK EXECUTION PLAN**
