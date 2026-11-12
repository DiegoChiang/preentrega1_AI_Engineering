"""Fragmentación de documentos con contexto solapado."""

import hashlib
import re

from incident_intelligence.rag.schemas import DocumentChunk, KnowledgeDocument


def count_lexical_tokens(text: str) -> int:
    """Cuenta palabras y signos sin depender de un tokenizador descargable."""

    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def split_documents(
    documents: list[KnowledgeDocument],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap debe ser menor que chunk_size")
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise RuntimeError("Instala la dependencia 'langchain-text-splitters'") from exc

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=count_lexical_tokens,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks: list[DocumentChunk] = []
    for document in documents:
        for index, text in enumerate(splitter.split_text(document.content)):
            digest = hashlib.sha256(
                f"{document.source}:{index}:{text}".encode()
            ).hexdigest()
            chunks.append(
                DocumentChunk(
                    id=digest,
                    content=text,
                    source=document.source,
                    chunk_index=index,
                    metadata={**document.metadata, "source": document.source, "chunk_index": index},
                )
            )
    return chunks

