"""Raw HTTP fetchers, one per feed kind. These return provider-native JSON/XML —
normalization into `NormalizedIncident` happens separately in `normalize.py` so
the two concerns (network I/O vs. shape-mapping) can be tested independently."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import httpx
import structlog

from aegis.ingestion.providers import FeedKind, Provider

log = structlog.get_logger(__name__)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


async def fetch_statuspage(client: httpx.AsyncClient, provider: Provider) -> list[dict]:
    resp = await client.get(provider.url, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    return data.get("incidents", [])


async def fetch_gcp(client: httpx.AsyncClient, provider: Provider) -> list[dict]:
    resp = await client.get(provider.url, timeout=_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    # GCP's incidents.json is a bare top-level array.
    return data if isinstance(data, list) else data.get("incidents", [])


async def fetch_aws(client: httpx.AsyncClient, provider: Provider) -> list[dict]:
    resp = await client.get(provider.url, timeout=_TIMEOUT)
    resp.raise_for_status()
    return _parse_rss_items(resp.text)


def _parse_rss_items(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iterfind(".//item"):
        items.append(
            {
                "guid": _text(item, "guid"),
                "title": _text(item, "title"),
                "link": _text(item, "link"),
                "description": _text(item, "description"),
                "pubDate": _text(item, "pubDate"),
            }
        )
    return items


def _text(item: ET.Element, tag: str) -> str | None:
    el = item.find(tag)
    return el.text.strip() if el is not None and el.text else None


_FETCHERS = {
    FeedKind.STATUSPAGE: fetch_statuspage,
    FeedKind.GCP_STATUS: fetch_gcp,
    FeedKind.AWS_HEALTH: fetch_aws,
}


async def fetch_raw(client: httpx.AsyncClient, provider: Provider) -> list[dict]:
    fetcher = _FETCHERS[provider.kind]
    try:
        return await fetcher(client, provider)
    except httpx.HTTPError as exc:
        log.warning("ingestion.fetch_failed", provider=provider.slug, error=str(exc))
        return []
