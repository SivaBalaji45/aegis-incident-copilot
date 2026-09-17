"""LangGraph state schema shared by every node. This is a state machine, not a
linear chain: the critic node can route back to retrieval (see graph.py's
conditional edge), so the state has to carry enough history (`critic_iterations`,
the last retrieval query) for that loop to terminate correctly."""

from __future__ import annotations

from typing import TypedDict

from aegis.guardrails.schemas import CriticVerdict, DiagnosisResult, DraftResult, TriageResult


class ChunkRef(TypedDict):
    chunk_id: str
    source_name: str
    content: str


class PipelineState(TypedDict, total=False):
    incident_id: str
    incident_title: str
    incident_body: str

    triage: TriageResult
    retrieval_query: str
    retrieved_chunks: list[ChunkRef]
    diagnosis: DiagnosisResult
    critic: CriticVerdict
    critic_iterations: int
    draft: DraftResult

    # terminal status the graph settles on: "drafted" | "needs_human_review"
    final_status: str
