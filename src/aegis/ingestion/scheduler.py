"""APScheduler wiring: poll on a fixed interval, hand new/changed incidents to
the agent pipeline. In-process scheduling is the right starting point for a
solo deployment — swap for Celery+Redis only if ingestion volume grows enough
that a poll cycle blocking on LLM calls actually becomes a problem (see
README's scale-path note)."""

from __future__ import annotations

import asyncio

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aegis.config import settings
from aegis.ingestion.poller import poll_once

log = structlog.get_logger(__name__)


async def _run_pipeline_for(incident_id: str) -> None:
    from aegis.agents.graph import run_pipeline  # local import: avoid import cycle at module load

    try:
        await run_pipeline(incident_id)
    except Exception:
        log.exception("scheduler.pipeline_failed", incident_id=incident_id)


async def _poll_and_dispatch() -> None:
    incidents = await poll_once()
    # Fire pipeline runs concurrently but don't let one slow incident block ingestion's
    # next cycle — the scheduler job itself returns once dispatch is done, not once
    # every pipeline run completes.
    if incidents:
        asyncio.create_task(
            asyncio.wait([asyncio.create_task(_run_pipeline_for(i.id)) for i in incidents])
        )


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _poll_and_dispatch,
        "interval",
        minutes=settings.aegis_poll_interval_minutes,
        id="poll_status_pages",
    )
    return scheduler
