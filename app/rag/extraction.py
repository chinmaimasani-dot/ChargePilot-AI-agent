"""Document text extraction for PDF, DOCX and text sources (Member 4)."""

from pathlib import Path


class DocumentExtractionError(Exception):
    pass


def extract_text(path: str | Path) -> str:
    """Extract raw text from a .pdf, .docx, .txt or .md document."""
    file_path = Path(path)
    if not file_path.exists():
        raise DocumentExtractionError(f"Document not found: {file_path.name}")

    suffix = file_path.suffix.lower()
    try:
        if suffix == ".pdf":
            return _extract_pdf(file_path)
        if suffix == ".docx":
            return _extract_docx(file_path)
        if suffix in {".txt", ".md", ".text"}:
            return file_path.read_text(encoding="utf-8", errors="replace")
        raise DocumentExtractionError(
            f"Unsupported document type '{suffix}'. Use PDF, DOCX or text."
        )
    except DocumentExtractionError:
        raise
    except Exception as exc:
        raise DocumentExtractionError(
            f"Could not extract text from {file_path.name}."
        ) from exc


def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            pages.append(text)
    return "\n\n".join(pages)


def _extract_docx(path: Path) -> str:
    import docx  # python-docx

    document = docx.Document(str(path))
    parts = []
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            parts.append(paragraph.text.strip())
    for table in document.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n\n".join(parts)
