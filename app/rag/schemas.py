"""Pydantic schemas for the knowledge pipeline (Member 4)."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    audience: Literal["owner", "driver"]
    source_name: str = Field(min_length=1, max_length=512)


class KnowledgeDocumentOut(BaseModel):
    id: uuid.UUID
    title: str
    audience: str
    source_name: str
    status: str
    chunk_count: int
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RetrievedChunk(BaseModel):
    title: str
    content: str
    score: float
    document_id: uuid.UUID
    chunk_index: int
