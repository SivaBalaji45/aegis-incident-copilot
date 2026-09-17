"""Retrieval node: embed the current query, vector-search pgvector, rerank
with the cross-encoder. Runs both on the initial pass (query from triage) and
on each critic-driven retry (query refined by the critic node)."""

from __future__ import annotations

from aegis.agents.state import ChunkRef, PipelineState
from aegis.db.session import session_scope
from aegis.rag.retriever import retrieve


async def retrieval_node(state: PipelineState) -> dict:
    query = state["retrieval_query"]
    async with session_scope() as session:
        chunks = await retrieve(session, query, top_k=5)

    refs: list[ChunkRef] = [
        {"chunk_id": c.id, "source_name": c.source_name, "content": c.content} for c in chunks
    ]
    return {"retrieved_chunks": refs}
