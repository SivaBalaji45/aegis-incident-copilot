"""Structured output contracts for each agent node. Every agent's raw LLM
output gets parsed into one of these before it's allowed onto the LangGraph
state — a malformed response fails loudly here instead of propagating a
half-shaped dict downstream."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TriageResult(BaseModel):
    severity: str = Field(description="one of: critical, major, minor, none")
    category: str = Field(description="e.g. network, database, auth, third-party-dependency")
    affected_services: list[str] = Field(default_factory=list)
    affected_regions: list[str] = Field(default_factory=list)
    error_codes: list[str] = Field(default_factory=list)


class Citation(BaseModel):
    chunk_id: str
    source_name: str
    quote: str


class DiagnosisResult(BaseModel):
    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[Citation] = Field(default_factory=list)


class CriticVerdict(BaseModel):
    grounded: bool
    groundedness_score: float = Field(ge=0.0, le=1.0)
    unsupported_claims: list[str] = Field(default_factory=list)
    refined_query: str | None = Field(
        default=None, description="set only when grounded=False and a retry is warranted"
    )
    notes: str = ""


class DraftResult(BaseModel):
    external_status_update: str
    internal_remediation_checklist: list[str] = Field(default_factory=list)
