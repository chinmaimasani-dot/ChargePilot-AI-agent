"""pgvector persistence and similarity search (Member 4)."""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.rag.models import KnowledgeChunk, KnowledgeDocument

logger = logging.getLogger(__name__)


def ensure_pgvector(session: Session) -> None:
    """Enable the pgvector extension (Neon ships it)."""
    session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    session.commit()


def save_document_with_chunks(
    *,
    title: str,
    audience: str,
    source_name: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> str:
    """Persist one processed document and its chunks; returns document id."""
    if len(chunks) != len(embeddings):
        raise ValueError("Chunk/embedding count mismatch.")

    with SessionLocal() as session:
        ensure_pgvector(session)
        document = KnowledgeDocument(
            title=title,
            audience=audience,
            source_name=source_name,
            status="PROCESSED",
            chunk_count=len(chunks),
        )
        session.add(document)
        session.flush()

        for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
            session.add(
                KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=content,
                    audience=audience,
                    chunk_metadata={
                        "title": title,
                        "source_name": source_name,
                        "audience": audience,
                    },
                    embedding=embedding,
                )
            )
        session.commit()
        return str(document.id)


def mark_document_failed(title: str, audience: str, source_name: str, error: str) -> None:
    with SessionLocal() as session:
        ensure_pgvector(session)
        session.add(
            KnowledgeDocument(
                title=title,
                audience=audience,
                source_name=source_name,
                status="FAILED",
                chunk_count=0,
                error=error[:2000],
            )
        )
        session.commit()


def similarity_search(
    query_embedding: list[float],
    *,
    audience: str,
    top_k: int,
    min_score: float,
) -> list[dict[str, Any]]:
    """Cosine-similarity search restricted to one role's knowledge collection.

    Role isolation is enforced in SQL via the audience filter, never by
    relying on the model or the caller.
    """
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT c.document_id, c.chunk_index, c.content, d.title,
                       1 - (c.embedding <=> :query) AS score
                FROM knowledge_chunks c
                JOIN knowledge_documents d ON d.id = c.document_id
                WHERE c.audience = :audience
                ORDER BY c.embedding <=> :query
                LIMIT :limit
                """
            ),
            {
                "query": str(query_embedding),
                "audience": audience,
                "limit": top_k,
            },
        ).mappings()

        return [
            {
                "document_id": str(row["document_id"]),
                "chunk_index": row["chunk_index"],
                "content": row["content"],
                "title": row["title"],
                "score": float(row["score"]),
            }
            for row in rows
            if float(row["score"]) >= min_score
        ]
