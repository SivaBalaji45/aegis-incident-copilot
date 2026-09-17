"""Sentence-embedding wrapper (HF task: Feature Extraction / Sentence Similarity).

Lazily loads a single `sentence-transformers` model per process — embedding
calls happen both at ingestion time (embedding knowledge chunks) and at query
time (embedding an incident for retrieval), so the model is loaded once and
reused rather than per-call.
"""

from __future__ import annotations

from functools import lru_cache

from aegis.config import settings


@lru_cache(maxsize=1)
def _model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.aegis_embedding_model)


def embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = _model().encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()


def embed_one(text: str) -> list[float]:
    return embed([text])[0]
