"""Ingest the knowledge_base/ collections into pgvector (Member 4).

Usage:
    python -m seed.ingest_knowledge                 # ingest everything
    python -m seed.ingest_knowledge --audience owner
    python -m seed.ingest_knowledge --file path/to/doc.pdf --audience driver

Requires RAG_EMBEDDING_* configuration for production embeddings; without a
key it falls back to the deterministic fake embedder (development only).
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def ingest_all(audience: str | None = None) -> None:
    from app.rag.ingestion import IngestionError, ingest_document

    base = PROJECT_ROOT / "knowledge_base"
    collections = [audience] if audience else ["owner", "driver"]

    for collection in collections:
        folder = base / collection
        if not folder.exists():
            print(f"Skipping missing folder: {folder}")
            continue
        for file_path in sorted(folder.iterdir()):
            if file_path.suffix.lower() not in {".txt", ".pdf", ".docx", ".md"}:
                continue
            try:
                result = ingest_document(file_path, audience=collection)
                print(f"OK  {collection}/{file_path.name}: {result['chunks']} chunks")
            except IngestionError as exc:
                print(f"FAILED {collection}/{file_path.name}: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge documents")
    parser.add_argument("--audience", choices=["owner", "driver"], default=None)
    parser.add_argument("--file", default=None, help="Ingest a single file")
    parser.add_argument("--title", default=None, help="Title when using --file")
    args = parser.parse_args()

    if args.file:
        from app.rag.ingestion import IngestionError, ingest_document

        target_audience = args.audience or "driver"
        try:
            result = ingest_document(args.file, audience=target_audience, title=args.title)
            print(f"OK: {result}")
        except IngestionError as exc:
            print(f"FAILED: {exc}")
            raise SystemExit(1)
    else:
        ingest_all(args.audience)


if __name__ == "__main__":
    main()
