"""Embedding generation (Member 4).

Embeddings use local sentence-transformers models (no API key needed, runs
on CPU). A deterministic hash-based fake is included for offline tests so
the pipeline never requires downloading model weights.
"""

import hashlib
import logging
from functools import lru_cache
from typing import Protocol

from app.rag.config import RAGSettings, get_rag_settings

logger = logging.getLogger(__name__)


class EmbeddingProvider(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class HashFakeEmbedder:
    """Deterministic offline embedder for tests (NOT for production)."""

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.md5(token.encode()).digest()
            index = digest[0] % self.dimensions
            vector[index] += 1.0
        norm = sum(vector) or 1.0
        return [v / norm for v in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class SentenceTransformerEmbedder:
    """Local sentence-transformers embeddings.

    The model is downloaded once on first use (Hugging Face) and cached
    locally; afterwards it runs fully offline on CPU.
    """

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self._model_name = model_name
        logger.info("Loading sentence-transformers model '%s'", model_name)
        self._model = SentenceTransformer(model_name)

    @property
    def dimensions(self) -> int:
        getter = getattr(
            self._model, "get_embedding_dimension", None
        ) or self._model.get_sentence_embedding_dimension
        return int(getter())

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return [v.tolist() for v in vectors]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


@lru_cache
def _get_sentence_transformer(model_name: str) -> SentenceTransformerEmbedder:
    """One shared model instance per process."""
    return SentenceTransformerEmbedder(model_name)


def get_embedder(settings: RAGSettings | None = None) -> EmbeddingProvider:
    """Resolve the embedder from settings (defaults to all-MiniLM-L6-v2)."""
    settings = settings or get_rag_settings()
    return _get_sentence_transformer(settings.sentence_transformers_model)
