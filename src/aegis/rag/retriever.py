"""Vector similarity search over `knowledge_chunks` (pgvector cosine distance),
followed by cross-encoder reranking. This is what the Retrieval agent node
calls; the Critic agent's retry path calls it again with a refined query."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.db.models import KnowledgeChunk
from aegis.rag.embeddings import embed_one
from aegis.rag.reranker import rerank


async def retrieve(
    session: AsyncSession,
    query: str,
    *,
    fetch_k: int = 20,
    top_k: int = 5,
) -> list[KnowledgeChunk]:
    query_vector = embed_one(query)
    stmt = (
        select(KnowledgeChunk)
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_vector))
        .limit(fetch_k)
    )
    candidates = list((await session.execute(stmt)).scalars().all())
    return rerank(query, candidates, top_k=top_k)
