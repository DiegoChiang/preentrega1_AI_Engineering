"""Contratos del flujo RAG."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1)
    source: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    content: str = Field(min_length=1)
    source: str
    chunk_index: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(DocumentChunk):
    score: float | None = None


class SourceReference(BaseModel):
    source: str
    chunk_id: str
    excerpt: str = Field(max_length=500)
    score: float | None = None


class RAGDraft(BaseModel):
    answer: str = Field(min_length=1, max_length=8000)
    grounded: bool
    confidence: float = Field(ge=0, le=1)


class RAGAnswer(RAGDraft):
    sources: list[SourceReference] = Field(default_factory=list)

