"""Fetch every provider, normalize, and upsert into `incidents`.

Runs standalone (`python -m aegis.ingestion.poller`) for local testing against
the real public APIs, and is wired into APScheduler by `scheduler.py` for
continuous polling. Returns the list of incidents that were newly inserted
(vs. merely updated) so the caller can decide whether to kick off the agent
pipeline.
"""

from __future__ import annotations

import asyncio

import httpx
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.db.models import Incident
from aegis.db.session import session_scope
from aegis.ingestion.fetchers import fetch_raw
from aegis.ingestion.normalize import normalize
from aegis.ingestion.providers import PROVIDERS
from aegis.ingestion.schemas import NormalizedIncident

log = structlog.get_logger(__name__)


async def fetch_all(client: httpx.AsyncClient) -> list[NormalizedIncident]:
    results: list[NormalizedIncident] = []
    raw_by_provider = await asyncio.gather(*(fetch_raw(client, p) for p in PROVIDERS))
    for provider, raw_incidents in zip(PROVIDERS, raw_by_provider):
        for raw in raw_incidents:
            try:
                results.append(normalize(raw, provider))
            except Exception:
                log.exception("ingestion.normalize_failed", provider=provider.slug)
    return results


async def upsert(session: AsyncSession, incident: NormalizedIncident) -> tuple[Incident, bool]:
    """Returns (row, is_new)."""
    stmt = select(Incident).where(
        Incident.provider_slug == incident.provider_slug,
        Incident.external_id == incident.external_id,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()

    if existing is None:
        row = Incident(
            provider_slug=incident.provider_slug,
            external_id=incident.external_id,
            title=incident.title,
            url=incident.url,
            status=incident.status,
            impact=incident.impact,
            started_at=incident.started_at,
            updated_at=incident.updated_at,
            resolved_at=incident.resolved_at,
            body_text=incident.body_text,
            raw=incident.raw,
        )
        session.add(row)
        return row, True

    changed = existing.status != incident.status or existing.body_text != incident.body_text
    existing.status = incident.status
    existing.impact = incident.impact
    existing.updated_at = incident.updated_at
    existing.resolved_at = incident.resolved_at
    existing.body_text = incident.body_text
    existing.raw = incident.raw
    if changed:
        # A status/body change on a known incident should re-enter the pipeline
        # too (e.g. a new update contradicts the earlier hypothesis) — the
        # scheduler checks this flag via pipeline_processed.
        existing.pipeline_processed = False
    return existing, False


async def poll_once() -> list[Incident]:
    """One full poll cycle. Returns incidents that are new or materially changed
    and therefore need the agent pipeline (re)run."""
    async with httpx.AsyncClient() as client:
        normalized = await fetch_all(client)

    needs_pipeline: list[Incident] = []
    async with session_scope() as session:
        for incident in normalized:
            row, is_new = await upsert(session, incident)
            if is_new or not row.pipeline_processed:
                needs_pipeline.append(row)
        await session.commit()

    log.info("ingestion.poll_complete", fetched=len(normalized), needs_pipeline=len(needs_pipeline))
    return needs_pipeline


if __name__ == "__main__":
    asyncio.run(poll_once())
