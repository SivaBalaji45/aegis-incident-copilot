"""The common shape every provider feed gets normalized into, regardless of
whether it started life as Statuspage JSON, GCP JSON, or an AWS RSS item."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NormalizedIncident(BaseModel):
    provider_slug: str
    external_id: str
    title: str
    url: str | None = None
    status: str = "unknown"
    impact: str | None = None
    started_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    body_text: str = ""
    raw: dict = {}

    @property
    def natural_key(self) -> tuple[str, str]:
        return (self.provider_slug, self.external_id)
