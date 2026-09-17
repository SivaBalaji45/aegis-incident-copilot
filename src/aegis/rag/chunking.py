"""Plain-text chunking for postmortems/runbooks already extracted to text.

PDF ingestion that needs to preserve table/layout structure (for the Document
QA HF task) is a separate, heavier path — see `rag/doc_ingest.py`.
"""

from __future__ import annotations


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """Fixed-size sliding-window chunking on whitespace-normalized text.
    Good enough for the golden-set corpus; swap for a semantic/recursive
    splitter (e.g. LangChain's) once chunk quality shows up as a retrieval
    bottleneck in the eval harness rather than before."""
    text = " ".join(text.split())
    if not text:
        return []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be greater than overlap")

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
