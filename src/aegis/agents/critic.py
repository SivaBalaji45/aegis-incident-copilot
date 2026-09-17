"""Critic node: checks the diagnosis's claims against the retrieved evidence
it cited. This is the self-verification step the whole project is built
around — "sounds plausible" and "is grounded" are checked as separate things.

The routing decision (retry vs. proceed vs. give up) lives in graph.py's
conditional edge, not here — this node's only job is to produce a verdict."""

from __future__ import annotations

from aegis.agents.diagnosis import _format_chunks
from aegis.agents.prompts import CRITIC_SYSTEM
from aegis.agents.state import PipelineState
from aegis.guardrails.schemas import CriticVerdict
from aegis.llm.parsing import parse_structured
from aegis.llm.router import generate


async def critic_node(state: PipelineState) -> dict:
    diagnosis = state["diagnosis"]
    prompt = (
        f"Hypothesis: {diagnosis.hypothesis}\n"
        f"Stated confidence: {diagnosis.confidence}\n\n"
        f"Citations offered:\n"
        + "\n".join(f"- [{c.chunk_id}] {c.source_name}: \"{c.quote}\"" for c in diagnosis.citations)
        + f"\n\nFull set of retrieved excerpts available to the diagnosis agent:\n{_format_chunks(state)}"
    )
    raw = await generate("strong", CRITIC_SYSTEM, prompt, max_tokens=768)
    verdict = parse_structured(raw, CriticVerdict)
    assert isinstance(verdict, CriticVerdict)

    iterations = state.get("critic_iterations", 0) + 1
    update: dict = {"critic": verdict, "critic_iterations": iterations}
    if verdict.refined_query:
        update["retrieval_query"] = verdict.refined_query
    return update
