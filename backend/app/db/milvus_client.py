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


# Global singleton instance
milvus_client = MilvusClient()


def get_milvus_collection(collection_name: str = None) -> Collection:
    """
    Milvus Collection을 가져오는 헬퍼 함수

    Args:
        collection_name: Collection 이름 (기본값: 환경 변수에서 로드)

    Returns:
        Collection: Milvus Collection 객체

    Raises:
        ValueError: Collection이 존재하지 않을 때
    """
    # 기본값: 환경 변수에서 로드
    if collection_name is None:
        collection_name = os.getenv("MILVUS_COLLECTION_NAME", "rag_document_chunks")
    if not connections.has_connection("default"):
        milvus_client.connect()

    if not utility.has_collection(collection_name):
        raise ValueError(f"Collection '{collection_name}'이 존재하지 않습니다")

    collection = Collection(collection_name)
    collection.load()

    return collection
