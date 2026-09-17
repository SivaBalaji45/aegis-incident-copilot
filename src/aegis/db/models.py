"""SQLAlchemy models.

Three tables carry the whole system: `incidents` (what the pollers write),
`knowledge_chunks` (the pgvector-backed RAG corpus of postmortems/runbooks),
and `diagnoses` (one row per agent-pipeline run against an incident, holding
the critic's verdict and the human-approval gate).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from aegis.config import settings


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (UniqueConstraint("provider_slug", "external_id", name="uq_incident_source"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    provider_slug: Mapped[str] = mapped_column(String(64), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="unknown")
    impact: Mapped[str | None] = mapped_column(String(32), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    body_text: Mapped[str] = mapped_column(Text, default="")
    raw: Mapped[dict] = mapped_column(JSON, default=dict)

    # Triage agent output (zero-shot classification + NER)
    triage_severity: Mapped[str | None] = mapped_column(String(32), nullable=True)
    triage_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    triage_entities: Mapped[dict] = mapped_column(JSON, default=dict)

    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_polled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    pipeline_processed: Mapped[bool] = mapped_column(default=False)

    diagnoses: Mapped[list[Diagnosis]] = relationship(back_populates="incident")


class KnowledgeChunk(Base):
    """One retrievable unit of a postmortem or runbook: a paragraph, a table,
    or — for multimodal sources — a page image reference. `embedding` is a
    dense vector used for the first-pass retrieval; the cross-encoder reranker
    in rag/reranker.py operates on the text after this stage, not the vector."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    source_type: Mapped[str] = mapped_column(String(32))  # "postmortem" | "runbook"
    source_name: Mapped[str] = mapped_column(String(255))
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    content: Mapped[str] = mapped_column(Text)
    chunk_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(settings.aegis_embedding_dim), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Diagnosis(Base):
    """One run of the agent pipeline against an incident. `critic_iterations`
    counts retrieve->diagnose->critic loops (capped by AEGIS_MAX_CRITIC_RETRIES);
    `status` is the human-approval gate — nothing in `draft_external_update`
    is ever published without a row here moving to "approved"."""

    __tablename__ = "diagnoses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    incident_id: Mapped[str] = mapped_column(ForeignKey("incidents.id"), index=True)
    incident: Mapped[Incident] = relationship(back_populates="diagnoses")

    hypothesis: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    citations: Mapped[list] = mapped_column(JSON, default=list)

    groundedness_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    critic_verdict: Mapped[str | None] = mapped_column(String(32), nullable=True)  # grounded|ungrounded
    critic_notes: Mapped[str] = mapped_column(Text, default="")
    critic_iterations: Mapped[int] = mapped_column(Integer, default=0)

    draft_external_update: Mapped[str] = mapped_column(Text, default="")
    draft_internal_checklist: Mapped[list] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(32), default="pending_review")
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
