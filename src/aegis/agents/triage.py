"""Triage node: zero-shot severity/category classification + entity extraction
(HF tasks: Zero-Shot Classification, Token Classification / NER), implemented
here as one structured-output LLM call rather than two separate model calls —
see README for why (a single frontier-model call at the "fast" tier beats the
latency/infra cost of hosting two separate HF pipelines for a portfolio-scale
incident volume; the HF task framing still describes what the call is doing)."""

from __future__ import annotations

from aegis.agents.prompts import TRIAGE_SYSTEM
from aegis.agents.state import PipelineState
from aegis.guardrails.schemas import TriageResult
from aegis.llm.parsing import parse_structured
from aegis.llm.router import generate


async def triage_node(state: PipelineState) -> dict:
    prompt = f"Title: {state['incident_title']}\n\nBody:\n{state['incident_body']}"
    raw = await generate("fast", TRIAGE_SYSTEM, prompt, max_tokens=512)
    triage = parse_structured(raw, TriageResult)
    assert isinstance(triage, TriageResult)

    query_terms = [state["incident_title"], triage.category, *triage.affected_services]
    retrieval_query = " ".join(t for t in query_terms if t)

    return {"triage": triage, "retrieval_query": retrieval_query}
