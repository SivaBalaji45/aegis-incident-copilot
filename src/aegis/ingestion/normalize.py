"""Maps each provider's native incident shape onto `NormalizedIncident`."""

from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime

from aegis.ingestion.providers import FeedKind, Provider
from aegis.ingestion.schemas import NormalizedIncident


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _parse_rfc822(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None


def normalize_statuspage(raw: dict, provider: Provider) -> NormalizedIncident:
    updates = raw.get("incident_updates", []) or []
    # Statuspage returns updates newest-first; keep that order for the body text
    # so agents read the latest status before older context.
    body_text = "\n\n".join(
        f"[{u.get('status', '')} @ {u.get('created_at', '')}] {u.get('body', '')}".strip()
        for u in updates
    )
    return NormalizedIncident(
        provider_slug=provider.slug,
        external_id=str(raw["id"]),
        title=raw.get("name", ""),
        url=raw.get("shortlink"),
        status=raw.get("status", "unknown"),
        impact=raw.get("impact"),
        started_at=_parse_iso(raw.get("created_at")),
        updated_at=_parse_iso(raw.get("updated_at")),
        resolved_at=_parse_iso(raw.get("resolved_at")),
        body_text=body_text or raw.get("name", ""),
        raw=raw,
    )


def normalize_gcp(raw: dict, provider: Provider) -> NormalizedIncident:
    updates = raw.get("updates", []) or []
    body_text = "\n\n".join(
        f"[{u.get('status', '')} @ {u.get('when', '')}] {u.get('text', '')}".strip()
        for u in updates
    ) or raw.get("external_desc", "")
    ended = raw.get("end")
    return NormalizedIncident(
        provider_slug=provider.slug,
        external_id=str(raw.get("id") or raw.get("number")),
        title=raw.get("external_desc", "")[:200] or "Untitled incident",
        url=raw.get("uri"),
        status="resolved" if ended else (raw.get("status_impact") or "unknown"),
        impact=raw.get("severity"),
        started_at=_parse_iso(raw.get("begin")),
        updated_at=_parse_iso(raw.get("modified") or raw.get("begin")),
        resolved_at=_parse_iso(ended),
        body_text=body_text,
        raw=raw,
    )


def normalize_aws(raw: dict, provider: Provider) -> NormalizedIncident:
    external_id = raw.get("guid") or raw.get("link") or raw.get("title", "")
    return NormalizedIncident(
        provider_slug=provider.slug,
        external_id=str(external_id),
        title=raw.get("title", "Untitled incident"),
        url=raw.get("link"),
        status="unknown",
        impact=None,
        started_at=_parse_rfc822(raw.get("pubDate")),
        updated_at=_parse_rfc822(raw.get("pubDate")),
        resolved_at=None,
        body_text=raw.get("description", "") or raw.get("title", ""),
        raw=raw,
    )


_NORMALIZERS = {
    FeedKind.STATUSPAGE: normalize_statuspage,
    FeedKind.GCP_STATUS: normalize_gcp,
    FeedKind.AWS_HEALTH: normalize_aws,
}


def normalize(raw: dict, provider: Provider) -> NormalizedIncident:
    return _NORMALIZERS[provider.kind](raw, provider)
