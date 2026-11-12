import pytest

from incident_intelligence.rag.schemas import RAGDraft, RetrievedChunk
from incident_intelligence.rag.service import RAGService


class FakeRepository:
    def __init__(self, chunks: list[RetrievedChunk]) -> None:
        self.chunks = chunks
        self.last_query: str | None = None
        self.last_k: int | None = None

    async def add(self, chunks: list[object]) -> None:
        return None

    async def delete(self, ids: list[str]) -> None:
        return None

    async def search(self, query: str, *, k: int) -> list[RetrievedChunk]:
        self.last_query = query
        self.last_k = k
        return self.chunks[:k]


class FakeGenerator:
    def __init__(self, draft: RAGDraft) -> None:
        self.draft = draft
        self.context: str | None = None

    async def generate(self, *, query: str, context: str) -> RAGDraft:
        self.context = context
        return self.draft


@pytest.mark.asyncio
async def test_supported_question_includes_sources() -> None:
    repository = FakeRepository(
        [
            RetrievedChunk(
                id="chunk-redis",
                content="Las claves de idempotencia se conservan durante 24 horas.",
                source="redis_idempotencia.txt",
                chunk_index=0,
                score=0.93,
            )
        ]
    )
    generator = FakeGenerator(
        RAGDraft(
            answer="Las claves de idempotencia se conservan durante 24 horas.",
            grounded=True,
            confidence=0.95,
        )
    )
    service = RAGService(repository, generator, top_k=4)

    result = await service.get_rag_response("¿Cuál es el TTL de las claves?")

    assert result.grounded is True
    assert result.sources[0].source == "redis_idempotencia.txt"
    assert result.sources[0].chunk_id == "chunk-redis"
    assert "24 horas" in result.sources[0].excerpt
    assert generator.context is not None and "redis_idempotencia.txt" in generator.context
    assert repository.last_k == 4


@pytest.mark.asyncio
async def test_question_without_retrieval_returns_explicit_unknown() -> None:
    repository = FakeRepository([])
    generator = FakeGenerator(
        RAGDraft(answer="No debe ejecutarse", grounded=False, confidence=0)
    )
    service = RAGService(repository, generator)

    result = await service.get_rag_response("¿Cuál es la contraseña de producción?")

    assert result.answer == "No lo sé con la información disponible."
    assert result.grounded is False
    assert result.sources == []
    assert generator.context is None


@pytest.mark.asyncio
async def test_ungrounded_generation_hides_retrieved_sources() -> None:
    repository = FakeRepository(
        [
            RetrievedChunk(
                id="chunk-api",
                content="La API usa Kubernetes.",
                source="runbook_api_pagos.md",
                chunk_index=0,
                score=0.5,
            )
        ]
    )
    generator = FakeGenerator(
        RAGDraft(
            answer="No lo sé con la información disponible.",
            grounded=False,
            confidence=0.05,
        )
    )

    result = await RAGService(repository, generator).get_rag_response(
        "¿Cuál es la contraseña de producción?"
    )

    assert result.grounded is False
    assert result.sources == []
