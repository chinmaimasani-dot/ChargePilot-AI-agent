"""RAG configuration (Member 4)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class RAGSettings(BaseSettings):
    """Embedding and retrieval settings.

    Embeddings run locally via sentence-transformers (CPU, no API key).
    `embedding_dimensions` must match the chosen model's native output
    dimension because the pgvector column is fixed at migration time:
      - all-MiniLM-L6-v2        -> 384
      - all-mpnet-base-v2       -> 768
      - BAAI/bge-small-en-v1.5  -> 384
      - BAAI/bge-large-en-v1.5  -> 1024
    """

    model_config = SettingsConfigDict(
        env_prefix="RAG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sentence_transformers_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    # Changing the model after ingesting documents requires re-indexing and
    # a migration to resize the vector column.

    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 4
    # Cosine-similarity threshold. Sentence-transformer relevant pairs
    # typically score 0.4-0.7; anything below the threshold is treated as
    # "no relevant evidence" and the assistant answers that it does not know.
    min_score: float = 0.35


@lru_cache
def get_rag_settings() -> RAGSettings:
    return RAGSettings()
