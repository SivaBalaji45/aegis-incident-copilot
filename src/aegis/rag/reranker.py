"""Cross-encoder reranking (HF task: Text Ranking).

The vector search in `retriever.py` is a fast, approximate first pass over
potentially thousands of chunks; the cross-encoder here scores the (query,
chunk) pair jointly and is far more accurate but too slow to run over the
full corpus — hence rerank only the top-k candidates retrieval already narrowed.
"""

from __future__ import annotations

from functools import lru_cache

from aegis.config import settings
from aegis.db.models import KnowledgeChunk


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(settings.aegis_reranker_model)


def rerank(query: str, candidates: list[KnowledgeChunk], top_k: int = 5) -> list[KnowledgeChunk]:
    if not candidates:
        return []
    pairs = [(query, c.content) for c in candidates]
    scores = _model().predict(pairs)
    ranked = sorted(zip(candidates, scores), key=lambda pair: pair[1], reverse=True)
    return [chunk for chunk, _ in ranked[:top_k]]
