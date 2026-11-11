"""Knowledge retrieval with role isolation (Member 4)."""

from typing import Any, Protocol

from app.rag.config import RAGSettings, get_rag_settings


class Retriever(Protocol):
    def retrieve(self, question: str, audience: str) -> list[dict[str, Any]]: ...


class KnowledgeRetriever:
    """Retrieves role-filtered knowledge chunks for grounding answers.

    `audience` is always the trusted role from backend context, so a driver
    can never retrieve owner knowledge and vice versa.
    """

    def __init__(
        self,
        embedder=None,
        search=None,
        settings: RAGSettings | None = None,
    ) -> None:
        self.settings = settings or get_rag_settings()
        self._embedder = embedder
        self._search = search

    def _ensure_embedder(self):
        if self._embedder is None:
            from app.rag.embeddings import get_embedder

            self._embedder = get_embedder()
        return self._embedder

    def _ensure_search(self):
        if self._search is None:
            from app.rag.vector_store import similarity_search

            self._search = similarity_search
        return self._search

    def retrieve(self, question: str, audience: str) -> list[dict[str, Any]]:
        if not question.strip():
            return []
        query_embedding = self._ensure_embedder().embed_query(question)
        results = self._ensure_search()(
            query_embedding,
            audience=audience,
            top_k=self.settings.top_k,
            min_score=self.settings.min_score,
        )
        # Enforce the evidence threshold here too so the rule holds even if a
        # search backend ignores min_score.
        return [
            {
                "title": r["title"],
                "content": r["content"],
                "score": r["score"],
                "document_id": r["document_id"],
                "chunk_index": r["chunk_index"],
            }
            for r in results
            if float(r.get("score", 0.0)) >= self.settings.min_score
        ]


def get_retriever() -> Retriever:
    """Process-wide retriever used by the chat runtime.

    Returns None-equivalent when the DB is not configured so the graph can
    still serve non-RAG routes during early integration.
    """
    try:
        return KnowledgeRetriever()
    except Exception:
        return KnowledgeRetriever(embedder=None, search=lambda *a, **k: [])
