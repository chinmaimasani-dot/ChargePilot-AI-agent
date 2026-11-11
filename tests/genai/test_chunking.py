"""Chunking and extraction tests (offline)."""

import pytest

from app.rag.chunking import chunk_text, clean_text


def test_clean_text_collapses_whitespace():
    cleaned = clean_text("Hello   world\n\n\n\nNext  paragraph")
    assert cleaned == "Hello world\n\nNext paragraph"


def test_chunk_text_produces_overlapping_chunks():
    text = ("\n\n".join(f"Paragraph {i} " + "content " * 40 for i in range(6)))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    settings_size = 1000
    for chunk in chunks:
        assert len(chunk) <= settings_size + 50  # small tolerance for separators


def test_chunk_text_empty():
    assert chunk_text("   ") == []


def test_chunk_metadata_fields():
    from app.rag.chunking import build_chunk_metadata

    meta = build_chunk_metadata(
        document_id="d1", title="T", audience="driver", source_name="f.txt"
    )
    assert meta == {
        "document_id": "d1",
        "title": "T",
        "audience": "driver",
        "source_name": "f.txt",
    }


def test_extract_text_unsupported_type(tmp_path):
    from app.rag.extraction import DocumentExtractionError, extract_text

    path = tmp_path / "doc.exe"
    path.write_text("nope", encoding="utf-8")
    with pytest.raises(DocumentExtractionError):
        extract_text(path)


def test_extract_text_missing_file():
    from app.rag.extraction import DocumentExtractionError, extract_text

    with pytest.raises(DocumentExtractionError):
        extract_text("does/not/exist.txt")


def test_extract_text_plain(tmp_path):
    from app.rag.extraction import extract_text

    path = tmp_path / "doc.txt"
    path.write_text("hello charging world", encoding="utf-8")
    assert extract_text(path) == "hello charging world"
