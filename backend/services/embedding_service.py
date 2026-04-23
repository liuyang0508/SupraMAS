"""
Embedding Service - Vector embeddings for RAG
Supports local sentence-transformers and cloud embedding APIs
"""

import logging
from typing import List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Unified Embedding Service

    Supports:
    - Local: sentence-transformers (BAAI/bge-large-zh-v1.5, etc.)
    - OpenAI: text-embedding-ada-002
    - Cohere: embed-multilingual-v3.0
    """

    def __init__(self):
        self._model = None
        self._model_name = None
        self._dimension = None
        self._initialized = False
        self._init_model()

    def _init_model(self):
        """Initialize embedding model"""
        from config.settings import config as app_config
        embed_cfg = app_config.llm

        model_name = embed_cfg.EMBEDDING_MODEL
        device = embed_cfg.EMBEDDING_DEVICE

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name, device=device)
            self._model_name = model_name
            self._dimension = self._model.get_sentence_embedding_dimension()
            self._initialized = True
            logger.info(f"[EmbeddingService] Loaded model '{model_name}' dim={self._dimension}")

        except ImportError:
            logger.warning("[EmbeddingService] sentence-transformers not installed, using mock")
        except Exception as e:
            logger.error(f"[EmbeddingService] Failed to load model: {e}")

    @property
    def is_available(self) -> bool:
        return self._initialized and self._model is not None

    @property
    def dimension(self) -> int:
        return self._dimension or 1024

    @property
    def model_name(self) -> str:
        return self._model_name or "unknown"

    def encode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """
        Encode texts to embeddings

        Args:
            texts: Single text or list of texts
            batch_size: Batch size for encoding
            normalize: Whether to L2-normalize embeddings

        Returns:
            numpy array of embeddings (shape: [num_texts, dimension])
        """
        if isinstance(texts, str):
            texts = [texts]

        if not self._model:
            logger.warning("[EmbeddingService] Model not available, returning mock embeddings")
            return np.random.randn(len(texts), self.dimension).astype(np.float32)

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False
        )
        return embeddings

    async def aencode(
        self,
        texts: Union[str, List[str]],
        batch_size: int = 32,
        normalize: bool = True
    ) -> np.ndarray:
        """Async wrapper for encode"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.encode, texts, batch_size, normalize)


# Global singleton
_embedding_service: Optional[EmbeddingService] = None

def get_embedding_service() -> EmbeddingService:
    """Get the global embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
