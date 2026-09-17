"""Incident and diagnosis endpoints, including the human-approval gate.

Nothing here ever pushes `draft_external_update` anywhere external — approval
just flips the DB row's status. Wiring an actual publish action (posting to
the company's own status page, Slack, etc.) is a deliberate later step, kept
separate so "approve" and "publish" can't be conflated into one click.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.api.schemas import DiagnosisOut, IncidentOut, ReviewDecision
from aegis.db.models import Diagnosis, Incident
from aegis.db.session import get_session

router = APIRouter()


@router.get("/incidents", response_model=list[IncidentOut])
async def list_incidents(
    status: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> list[Incident]:
    stmt = select(Incident).order_by(Incident.first_seen_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Incident.status == status)
    return list((await session.execute(stmt)).scalars().all())


@router.get("/incidents/{incident_id}", response_model=IncidentOut)
async def get_incident(incident_id: str, session: AsyncSession = Depends(get_session)) -> Incident:
    incident = await session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.get("/incidents/{incident_id}/diagnoses", response_model=list[DiagnosisOut])
async def list_diagnoses_for_incident(
    incident_id: str, session: AsyncSession = Depends(get_session)
) -> list[Diagnosis]:
    stmt = (
        select(Diagnosis)
        .where(Diagnosis.incident_id == incident_id)
        .order_by(Diagnosis.created_at.desc())
    )
    return list((await session.execute(stmt)).scalars().all())


@router.get("/diagnoses/{diagnosis_id}", response_model=DiagnosisOut)
async def get_diagnosis(diagnosis_id: str, session: AsyncSession = Depends(get_session)) -> Diagnosis:
    diagnosis = await session.get(Diagnosis, diagnosis_id)
    if diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return diagnosis


@router.post("/diagnoses/{diagnosis_id}/review", response_model=DiagnosisOut)
async def review_diagnosis(
    diagnosis_id: str,
    decision: ReviewDecision,
    session: AsyncSession = Depends(get_session),
) -> Diagnosis:
    diagnosis = await session.get(Diagnosis, diagnosis_id)
    if diagnosis is None:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    if diagnosis.status not in ("pending_review", "needs_human_review"):
        raise HTTPException(status_code=409, detail=f"Diagnosis already {diagnosis.status}")

    diagnosis.status = "approved" if decision.approve else "rejected"
    diagnosis.reviewed_by = decision.reviewer
    if decision.notes:
        diagnosis.critic_notes = f"{diagnosis.critic_notes}\n\n[reviewer note] {decision.notes}"

    await session.commit()
    await session.refresh(diagnosis)
    return diagnosis
