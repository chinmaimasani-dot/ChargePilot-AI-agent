"""member4 knowledge documents and chunks with pgvector

Revision ID: dac2e54e4307
Revises: 20261104_0001
Create Date: 2026-11-10 11:42:19.897040

Member 4 migration: knowledge_documents metadata + knowledge_chunks with
pgvector embeddings. Role isolation uses the audience column; embedding
dimension comes from RAG_EMBEDDING_DIMENSIONS (default 1536).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from pgvector.sqlalchemy import Vector

from app.rag.config import get_rag_settings


# revision identifiers, used by Alembic.
revision: str = 'dac2e54e4307'
down_revision: Union[str, Sequence[str], None] = '20261104_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = get_rag_settings().embedding_dimensions


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        'knowledge_documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('audience', sa.String(length=20), nullable=False),
        sa.Column('source_name', sa.String(length=512), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('chunk_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_knowledge_documents_audience'), 'knowledge_documents', ['audience'])

    op.create_table(
        'knowledge_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('document_id', UUID(as_uuid=True),
                  sa.ForeignKey('knowledge_documents.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('audience', sa.String(length=20), nullable=False),
        sa.Column('chunk_metadata', JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index(op.f('ix_knowledge_chunks_document_id'), 'knowledge_chunks', ['document_id'])
    op.create_index('ix_knowledge_chunks_audience_doc', 'knowledge_chunks', ['audience', 'document_id'])
    op.create_index(
        'ix_knowledge_chunks_embedding_hnsw',
        'knowledge_chunks',
        ['embedding'],
        postgresql_using='hnsw',
        postgresql_ops={'embedding': 'vector_cosine_ops'},
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_knowledge_chunks_embedding_hnsw', table_name='knowledge_chunks')
    op.drop_index('ix_knowledge_chunks_audience_doc', table_name='knowledge_chunks')
    op.drop_index(op.f('ix_knowledge_chunks_document_id'), table_name='knowledge_chunks')
    op.drop_table('knowledge_chunks')
    op.drop_index(op.f('ix_knowledge_documents_audience'), table_name='knowledge_documents')
    op.drop_table('knowledge_documents')
