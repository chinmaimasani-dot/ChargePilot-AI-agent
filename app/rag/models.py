"""Knowledge-base persistence models (Member 4).

`knowledge_documents` metadata and ingestion status fields are coordinated
with Member 1; these tables are authored in this Member 4 migration. Dynamic
application data (stations, chargers, pricing, sessions, bookings) must
never be stored or answered from here — RAG serves static knowledge only.
"""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.rag.config import get_rag_settings


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # Logical knowledge collection: "owner" or "driver" (role isolation).
    audience: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(512), nullable=False)
    # PENDING | PROCESSED | FAILED
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    chunk_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    embedding = mapped_column(
        Vector(get_rag_settings().embedding_dimensions), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


Index(
    "ix_knowledge_chunks_audience_doc",
    KnowledgeChunk.audience,
    KnowledgeChunk.document_id,
)
