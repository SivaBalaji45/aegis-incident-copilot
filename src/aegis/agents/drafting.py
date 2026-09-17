"""Response-drafting node: produces the external status update and internal
checklist. Only reached once the critic has approved the diagnosis as
grounded — see graph.py. Output still lands as `status=pending_review` in the
DB; nothing here publishes anything."""

from __future__ import annotations

from aegis.agents.prompts import DRAFT_SYSTEM
from aegis.agents.state import PipelineState
from aegis.guardrails.schemas import DraftResult
from aegis.llm.parsing import parse_structured
from aegis.llm.router import generate


async def drafting_node(state: PipelineState) -> dict:
    diagnosis = state["diagnosis"]
    citations_text = "\n".join(
        f"- [{c.chunk_id}] {c.source_name}: \"{c.quote}\"" for c in diagnosis.citations
    )
    prompt = (
        f"Incident: {state['incident_title']}\n"
        f"Grounded hypothesis: {diagnosis.hypothesis}\n"
        f"Confidence: {diagnosis.confidence}\n\n"
        f"Supporting citations:\n{citations_text}"
    )
    raw = await generate("strong", DRAFT_SYSTEM, prompt, max_tokens=768)
    draft = parse_structured(raw, DraftResult)
    assert isinstance(draft, DraftResult)
    return {"draft": draft, "final_status": "drafted"}
