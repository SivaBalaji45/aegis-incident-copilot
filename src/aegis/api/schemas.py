"""API request/response models — deliberately separate from the SQLAlchemy
models in db/models.py so the wire format can evolve independently of storage."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider_slug: str
    title: str
    url: str | None
    status: str
    impact: str | None
    triage_severity: str | None
    triage_category: str | None
    started_at: datetime | None
    updated_at: datetime | None
    pipeline_processed: bool


class DiagnosisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    hypothesis: str
    confidence: float
    citations: list
    groundedness_score: float | None
    critic_verdict: str | None
    critic_iterations: int
    draft_external_update: str
    draft_internal_checklist: list
    status: str
    reviewed_by: str | None
    created_at: datetime


class ReviewDecision(BaseModel):
    reviewer: str
    approve: bool
    notes: str | None = None
