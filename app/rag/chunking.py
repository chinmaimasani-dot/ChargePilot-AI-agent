"""Content cleaning and chunking with metadata tagging (Member 4)."""

import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.rag.config import get_rag_settings


def clean_text(text: str) -> str:
    """Light normalization: collapse whitespace, drop control characters."""
    text = re.sub(r"\x00|\x1c|\x1d|\x1e|\x1f", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    """Split cleaned text into overlapping chunks using the configured sizes."""
    cleaned = clean_text(text)
    if not cleaned:
        return []
    settings = get_rag_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [chunk.strip() for chunk in splitter.split_text(cleaned) if chunk.strip()]


def build_chunk_metadata(
    *, document_id: str, title: str, audience: str, source_name: str
) -> dict:
    """Metadata attached to every chunk of a document (used for role filters)."""
    return {
        "document_id": document_id,
        "title": title,
        "audience": audience,
        "source_name": source_name,
    }
