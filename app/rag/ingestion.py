"""Document ingestion pipeline (Member 4).

extract → clean → chunk → embed → persist (pgvector) with status tracking in
`knowledge_documents`. Dynamic application data never enters this pipeline.
"""

import logging
from pathlib import Path

from app.rag.chunking import chunk_text, clean_text

logger = logging.getLogger(__name__)


class IngestionError(Exception):
    pass


def ingest_document(path: str | Path, audience: str, title: str | None = None) -> dict:
    """Ingest one knowledge document for the given audience collection.

    Returns {"document_id", "chunks"} on success; raises IngestionError with
    a safe message on failure (and records the failure in the DB).
    """
    from app.rag.embeddings import get_embedder
    from app.rag.extraction import DocumentExtractionError, extract_text
    from app.rag.vector_store import mark_document_failed, save_document_with_chunks

    file_path = Path(path)

    if audience not in {"owner", "driver"}:
        raise IngestionError("Audience must be 'owner' or 'driver'.")

    resolved_title = title or file_path.stem
    try:
        raw_text = extract_text(file_path)
    except DocumentExtractionError as exc:
        from app.rag.vector_store import mark_document_failed as _mark

        try:
            _mark(resolved_title, audience, file_path.name, str(exc))
        except Exception:
            logger.exception("Could not record failed ingestion")
        raise IngestionError(str(exc)) from exc

    cleaned = clean_text(raw_text)
    chunks = chunk_text(cleaned)
    if not chunks:
        message = "Document produced no content to index."
        try:
            mark_document_failed(resolved_title, audience, file_path.name, message)
        except Exception:
            logger.exception("Could not record failed ingestion")
        raise IngestionError(message)

    try:
        embedder = get_embedder()
        embeddings = embedder.embed_documents(chunks)
    except Exception as exc:
        message = "Embedding model failed; document was not indexed."
        try:
            mark_document_failed(resolved_title, audience, file_path.name, message)
        except Exception:
            logger.exception("Could not record failed ingestion")
        logger.exception("Embedding failure")
        raise IngestionError(message) from exc

    document_id = save_document_with_chunks(
        title=resolved_title,
        audience=audience,
        source_name=file_path.name,
        chunks=chunks,
        embeddings=embeddings,
    )
    return {"document_id": document_id, "chunks": len(chunks)}
