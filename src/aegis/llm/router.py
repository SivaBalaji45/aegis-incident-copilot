"""Cost-aware model routing.

Each agent node asks for a *tier* ("fast" | "strong"), not a model name — the
mapping from tier to actual model id lives here, in one place, so swapping
providers or rebalancing cost/quality later is a config change, not a
find-and-replace across every agent. Anthropic is the default provider; the
`generate` signature deliberately doesn't leak Anthropic-specific types so a
second provider could be added behind the same interface.
"""

from __future__ import annotations

from typing import Literal

import structlog
from anthropic import AsyncAnthropic

from aegis.config import settings

log = structlog.get_logger(__name__)

Tier = Literal["fast", "strong"]

_TIER_TO_MODEL = {
    "fast": settings.aegis_triage_model,
    "strong": settings.aegis_diagnosis_model,
}

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def generate(
    tier: Tier,
    system: str,
    prompt: str,
    *,
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Single-shot text generation. Every agent node should call this rather
    than instantiating its own client, so tracing/cost-logging stays centralized."""
    model = _TIER_TO_MODEL[tier]
    client = _get_client()
    response = await client.messages.create(
        model=model,
        system=system,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    log.info(
        "llm.generate",
        tier=tier,
        model=model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )
    return text
