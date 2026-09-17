"""Wires the five agent nodes into a LangGraph state machine — a graph, not a
linear chain, because the critic can route back to retrieval.

    triage -> retrieval -> diagnosis -> critic --grounded--> draft -> END
                  ^                        |
                  '------ungrounded, retries remain

If the critic still isn't satisfied after AEGIS_MAX_CRITIC_RETRIES, the graph
stops short of drafting and the incident is flagged "needs_human_review"
rather than looping forever or shipping a shaky answer.
"""

from __future__ import annotations

import structlog
from langgraph.graph import END, StateGraph

from aegis.agents.critic import critic_node
from aegis.agents.diagnosis import diagnosis_node
from aegis.agents.drafting import drafting_node
from aegis.agents.retrieval import retrieval_node
from aegis.agents.state import PipelineState
from aegis.agents.triage import triage_node
from aegis.config import settings
from aegis.db.models import Diagnosis, Incident
from aegis.db.session import session_scope
from aegis.guardrails.pii import redact

log = structlog.get_logger(__name__)


def _route_after_critic(state: PipelineState) -> str:
    verdict = state["critic"]
    if verdict.grounded:
        return "draft"
    if state.get("critic_iterations", 0) >= settings.aegis_max_critic_retries:
        return "give_up"
    return "retry"


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("triage", triage_node)
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("diagnosis", diagnosis_node)
    graph.add_node("critic", critic_node)
    graph.add_node("draft", drafting_node)

    graph.set_entry_point("triage")
    graph.add_edge("triage", "retrieval")
    graph.add_edge("retrieval", "diagnosis")
    graph.add_edge("diagnosis", "critic")
    graph.add_conditional_edges(
        "critic",
        _route_after_critic,
        {"draft": "draft", "retry": "retrieval", "give_up": END},
    )
    graph.add_edge("draft", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_pipeline(incident_id: str) -> str:
    """Loads the incident, runs the full agent graph, and persists a
    `Diagnosis` row (status=pending_review, or needs_human_review if the
    critic never reached groundedness). Returns the diagnosis id."""
    async with session_scope() as session:
        incident = await session.get(Incident, incident_id)
        if incident is None:
            raise ValueError(f"No incident with id={incident_id!r}")

        initial_state: PipelineState = {
            "incident_id": incident.id,
            "incident_title": incident.title,
            "incident_body": redact(incident.body_text),
            "critic_iterations": 0,
        }

    final_state: PipelineState = await get_graph().ainvoke(initial_state)

    diagnosis_obj = final_state.get("diagnosis")
    critic = final_state.get("critic")
    draft = final_state.get("draft")
    reached_draft = final_state.get("final_status") == "drafted"

    async with session_scope() as session:
        row = Diagnosis(
            incident_id=incident_id,
            hypothesis=diagnosis_obj.hypothesis if diagnosis_obj else "",
            confidence=diagnosis_obj.confidence if diagnosis_obj else 0.0,
            citations=[c.model_dump() for c in diagnosis_obj.citations] if diagnosis_obj else [],
            groundedness_score=critic.groundedness_score if critic else None,
            critic_verdict="grounded" if (critic and critic.grounded) else "ungrounded",
            critic_notes=critic.notes if critic else "",
            critic_iterations=final_state.get("critic_iterations", 0),
            draft_external_update=draft.external_status_update if draft else "",
            draft_internal_checklist=draft.internal_remediation_checklist if draft else [],
            status="pending_review" if reached_draft else "needs_human_review",
        )
        session.add(row)

        incident = await session.get(Incident, incident_id)
        if incident is not None:
            incident.pipeline_processed = True

        await session.commit()
        log.info(
            "pipeline.completed",
            incident_id=incident_id,
            diagnosis_id=row.id,
            status=row.status,
            critic_iterations=row.critic_iterations,
        )
        return row.id
