from aegis.ingestion.normalize import normalize_aws, normalize_gcp, normalize_statuspage
from aegis.ingestion.providers import get_provider
from aegis.rag.chunking import chunk_text


def test_normalize_statuspage_orders_updates_and_parses_dates():
    provider = get_provider("github")
    raw = {
        "id": "abc123",
        "name": "Degraded performance",
        "shortlink": "https://stspg.io/abc123",
        "status": "resolved",
        "impact": "minor",
        "created_at": "2024-06-01T12:00:00.000Z",
        "updated_at": "2024-06-01T13:00:00.000Z",
        "resolved_at": "2024-06-01T13:00:00.000Z",
        "incident_updates": [
            {"status": "resolved", "created_at": "2024-06-01T13:00:00Z", "body": "Resolved."},
            {"status": "investigating", "created_at": "2024-06-01T12:00:00Z", "body": "Looking into it."},
        ],
    }

    incident = normalize_statuspage(raw, provider)

    assert incident.provider_slug == "github"
    assert incident.external_id == "abc123"
    assert incident.status == "resolved"
    assert incident.started_at.year == 2024
    assert "Resolved." in incident.body_text
    assert incident.body_text.index("resolved") < incident.body_text.index("investigating")


def test_normalize_gcp_falls_back_to_external_desc_when_no_updates():
    provider = get_provider("gcp")
    raw = {
        "id": "gcp-1",
        "external_desc": "Cloud Storage elevated latency",
        "uri": "https://status.cloud.google.com/incidents/gcp-1",
        "severity": "medium",
        "begin": "2024-06-01T00:00:00Z",
        "end": None,
        "updates": [],
    }

    incident = normalize_gcp(raw, provider)

    assert incident.external_id == "gcp-1"
    assert incident.status == "unknown"
    assert incident.body_text == "Cloud Storage elevated latency"


def test_normalize_aws_parses_rfc822_pubdate():
    provider = get_provider("aws")
    raw = {
        "guid": "aws-guid-1",
        "title": "Increased error rates in us-east-1",
        "link": "https://status.aws.amazon.com/#aws-guid-1",
        "description": "Some EC2 API calls are failing in us-east-1.",
        "pubDate": "Sat, 01 Jun 2024 12:00:00 PDT",
    }

    incident = normalize_aws(raw, provider)

    assert incident.provider_slug == "aws"
    assert incident.started_at is not None
    assert incident.started_at.year == 2024


def test_chunk_text_respects_overlap_and_size():
    text = "word " * 500
    chunks = chunk_text(text, chunk_size=100, overlap=20)

    assert all(len(c) <= 100 for c in chunks)
    assert len(chunks) > 1
    # consecutive chunks should share the overlap region
    assert chunks[0][-20:] == chunks[1][:20]


def test_chunk_text_empty_input_returns_no_chunks():
    assert chunk_text("") == []
