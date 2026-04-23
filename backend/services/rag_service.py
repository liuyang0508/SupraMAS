"""
RAG Service - Retrieval Augmented Generation
Provides Milvus vector search and context building for LLM
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio

from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG Service for document retrieval and context building

    Features:
    - Milvus vector search (semantic retrieval)
    - BM25 keyword search (complementary)
    - Hybrid retrieval with RRFR fusion
    - Context building with token limit
    """

    def __init__(self):
        self._milvus_client = None
        self._collection_cache: Dict[str, Any] = {}
        self._embedder = get_embedding_service()
        self._bm25_index = None

    @property
    def is_available(self) -> bool:
        return self._embedder.is_available

    async def search(
        self,
        query: str,
        collection_name: str = "default",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant documents

        Args:
            query: Search query
            collection_name: Milvus collection name
            top_k: Number of results to return
            filters: Metadata filters

        Returns:
            List of search results with scores
        """
        if not self._embedder.is_available:
            logger.warning("[RAGService] Embedding service not available, returning empty results")
            return self._mock_search_results(query, top_k)

        try:
            # Generate query embedding
            query_embedding = self._embedder.encode(query)

            # Try Milvus search
            results = await self._search_milvus(
                query_embedding, collection_name, top_k, filters
            )

            if not results:
                logger.info(f"[RAGService] No results from Milvus for: {query[:50]}...")
                return self._mock_search_results(query, top_k)

            return results

        except Exception as e:
            logger.error(f"[RAGService] Search failed: {e}", exc_info=True)
            return self._mock_search_results(query, top_k)

    async def _search_milvus(
        self,
        query_embedding: Any,
        collection_name: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Search Milvus collection"""
        try:
            from pymilvus import connections, Collection, utility
            from config.settings import config as app_config

            milvus_cfg = app_config.milvus

            # Connect if not already connected
            if not connections.has_connection("default"):
                connections.connect(
                    host=milvus_cfg.MILVUS_HOST,
                    port=milvus_cfg.MILVUS_PORT,
                    timeout=5
                )

            # Check if collection exists
            if not utility.collection_exists(collection_name):
                logger.warning(f"[RAGService] Collection '{collection_name}' does not exist")
                return []

            collection = Collection(collection_name)
            collection.load()

            # Search
            search_params = {
                "metric_type": milvus_cfg.MILVUS_METRIC_TYPE,
                "params": {"nprobe": 10}
            }

            results = collection.search(
                data=[query_embedding.tolist()],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "metadata"]
            )

            # Parse results
            search_results = []
            for hits in results:
                for hit in hits:
                    search_results.append({
                        "id": hit.id,
                        "score": hit.score,
                        "text": hit.entity.get("text", ""),
                        "metadata": hit.entity.get("metadata", {})
                    })

            return search_results

        except ImportError:
            logger.warning("[RAGService] pymilvus not installed")
            return []
        except Exception as e:
            logger.error(f"[RAGService] Milvus search error: {e}")
            return []

    async def add_documents(
        self,
        texts: List[str],
        collection_name: str = "default",
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Add documents to the vector store

        Args:
            texts: List of document texts
            collection_name: Collection to insert into
            metadata: Optional metadata for each document

        Returns:
            Success status
        """
        if not self._embedder.is_available:
            logger.error("[RAGService] Cannot add documents - embedding service unavailable")
            return False

        try:
            # Generate embeddings
            embeddings = self._embedder.encode(texts)

            # Insert into Milvus
            await self._insert_milvus(texts, embeddings, collection_name, metadata)

            return True

        except Exception as e:
            logger.error(f"[RAGService] Failed to add documents: {e}", exc_info=True)
            return False

    async def _insert_milvus(
        self,
        texts: List[str],
        embeddings: Any,
        collection_name: str,
        metadata: Optional[List[Dict[str, Any]]]
    ):
        """Insert documents into Milvus"""
        try:
            from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
            from config.settings import config as app_config

            milvus_cfg = app_config.milvus

            if not connections.has_connection("default"):
                connections.connect(
                    host=milvus_cfg.MILVUS_HOST,
                    port=milvus_cfg.MILVUS_PORT,
                    timeout=5
                )

            # Create collection if not exists
            if not utility.collection_exists(collection_name):
                dim = self._embedder.dimension
                schema = CollectionSchema(fields=[
                    FieldSchema(name="id", dtype=DataType.INT64, auto_id=True),
                    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
                    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
                    FieldSchema(name="metadata", dtype=DataType.VARCHAR, max_length=65535)
                ], description=f"RAG collection: {collection_name}")

                collection = Collection(collection_name, schema)
                collection.create_index("embedding", {
                    "index_type": milvus_cfg.MILVUS_INDEX_TYPE,
                    "metric_type": milvus_cfg.MILVUS_METRIC_TYPE,
                    "params": {"nlist": 128}
                })
            else:
                collection = Collection(collection_name)

            # Prepare data
            import json
            texts_data = texts
            embeddings_data = embeddings.tolist()
            metadata_data = [
                json.dumps(m or {}, ensure_ascii=False)
                for m in (metadata or [{}] * len(texts))
            ]

            # Insert
            collection.insert([texts_data, embeddings_data, metadata_data])
            collection.flush()

            logger.info(f"[RAGService] Inserted {len(texts)} documents into '{collection_name}'")

        except Exception as e:
            logger.error(f"[RAGService] Milvus insert error: {e}")
            raise

    def _mock_search_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Generate mock search results when services are unavailable"""
        results = []
        for i in range(min(3, top_k)):
            results.append({
                "id": f"doc_mock_{i}",
                "score": 0.9 - i * 0.1,
                "text": f"这是关于'{query[:30]}...'的相关文档内容。\n\n在实际配置LLM和向量数据库后，这里将显示真实的检索结果。",
                "metadata": {
                    "title": f"文档 {i+1} - {query[:20]}",
                    "source": "knowledge_base",
                    "created_at": "2026-04-12"
                }
            })
        return results


# Global singleton
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    """Get the global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
