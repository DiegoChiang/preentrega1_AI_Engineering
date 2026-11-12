"""Ingesta y consulta del sistema RAG local."""

import argparse
import asyncio
import json

from incident_intelligence.config import Settings
from incident_intelligence.integrations.langchain import build_openai_embeddings
from incident_intelligence.rag.generation import build_answer_generator
from incident_intelligence.rag.ingestion import RAGIngestor
from incident_intelligence.rag.repository import ChromaRepository
from incident_intelligence.rag.service import RAGService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gestiona la base de conocimiento local")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("ingest", help="Indexa archivos .txt y .md")
    query_parser = subparsers.add_parser("query", help="Consulta la base vectorial")
    query_parser.add_argument("question")
    return parser


def build_repository(settings: Settings) -> ChromaRepository:
    return ChromaRepository(
        collection_name=settings.chroma_collection,
        persist_directory=str(settings.chroma_persist_dir),
        embedding_function=build_openai_embeddings(settings),
    )


async def run(command: str, question: str | None = None) -> None:
    settings = Settings()
    repository = build_repository(settings)

    if command == "ingest":
        ingestor = RAGIngestor(
            repository,
            data_dir=settings.data_dir,
            manifest_path=settings.chroma_persist_dir / "manifest.json",
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
        )
        result = await ingestor.ingest()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if question is None:
        raise ValueError("La consulta requiere una pregunta")
    service = RAGService(
        repository,
        build_answer_generator(settings),
        top_k=settings.rag_top_k,
        min_relevance_score=settings.rag_min_relevance_score,
    )
    result = await service.get_rag_response(question)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2))


def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run(args.command, getattr(args, "question", None)))


if __name__ == "__main__":
    main()
