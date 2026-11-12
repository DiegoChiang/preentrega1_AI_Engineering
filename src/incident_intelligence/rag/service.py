"""Flujo asíncrono end-to-end de recuperación y generación."""

from incident_intelligence.rag.generation import AnswerGenerator
from incident_intelligence.rag.repository import VectorRepository
from incident_intelligence.rag.schemas import RAGAnswer, SourceReference


class RAGService:
    def __init__(
        self,
        repository: VectorRepository,
        generator: AnswerGenerator,
        *,
        top_k: int = 4,
        min_relevance_score: float = 0.3,
    ) -> None:
        self.repository = repository
        self.generator = generator
        self.top_k = top_k
        self.min_relevance_score = min_relevance_score

    async def get_rag_response(self, query: str) -> RAGAnswer:
        clean = query.strip()
        if not clean:
            raise ValueError("La consulta no puede estar vacía")

        chunks = await self.repository.search(clean, k=self.top_k)
        chunks = [
            chunk
            for chunk in chunks
            if chunk.score is None or chunk.score >= self.min_relevance_score
        ]
        if not chunks:
            return RAGAnswer(
                answer="No lo sé con la información disponible.",
                grounded=False,
                confidence=0,
                sources=[],
            )

        context = "\n\n".join(
            f"[Fuente: {chunk.source} | Fragmento: {chunk.id}]\n{chunk.content}"
            for chunk in chunks
        )
        draft = await self.generator.generate(query=clean, context=context)
        sources = []
        if draft.grounded:
            sources = [
                SourceReference(
                    source=chunk.source,
                    chunk_id=chunk.id,
                    excerpt=chunk.content[:500],
                    score=chunk.score,
                )
                for chunk in chunks
            ]
        return RAGAnswer(**draft.model_dump(), sources=sources)


async def get_rag_response(
    query: str,
    repository: VectorRepository,
    generator: AnswerGenerator,
    *,
    top_k: int = 4,
    min_relevance_score: float = 0.3,
) -> RAGAnswer:
    return await RAGService(
        repository,
        generator,
        top_k=top_k,
        min_relevance_score=min_relevance_score,
    ).get_rag_response(query)

