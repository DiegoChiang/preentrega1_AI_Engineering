"""Carga de documentos de conocimiento desde disco."""

from pathlib import Path

from incident_intelligence.rag.schemas import KnowledgeDocument

SUPPORTED_SUFFIXES = {".txt", ".md"}


def load_knowledge_documents(data_dir: Path) -> list[KnowledgeDocument]:
    if not data_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta de datos: {data_dir}")

    documents: list[KnowledgeDocument] = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        source = path.relative_to(data_dir).as_posix()
        documents.append(
            KnowledgeDocument(
                content=content,
                source=source,
                metadata={"suffix": path.suffix.lower(), "title": path.stem},
            )
        )
    return documents

