import pytest

from aegis.guardrails.pii import redact
from aegis.guardrails.schemas import TriageResult
from aegis.llm.parsing import StructuredOutputError, parse_structured


def test_redact_strips_email_ip_and_phone():
    text = "Contact ops@example.com or 192.168.1.10, call 415-555-0199 for help."
    redacted = redact(text)

    assert "ops@example.com" not in redacted
    assert "192.168.1.10" not in redacted
    assert "415-555-0199" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_IP]" in redacted


def test_parse_structured_handles_fenced_json():
    raw = '```json\n{"severity": "major", "category": "network", "affected_services": ["api"], "affected_regions": [], "error_codes": []}\n```'
    result = parse_structured(raw, TriageResult)

    assert isinstance(result, TriageResult)
    assert result.severity == "major"
    assert result.affected_services == ["api"]


def test_parse_structured_handles_bare_json():
    raw = '{"severity": "minor", "category": "auth", "affected_services": [], "affected_regions": [], "error_codes": []}'
    result = parse_structured(raw, TriageResult)

    assert result.category == "auth"


def test_parse_structured_raises_on_invalid_json():
    with pytest.raises(StructuredOutputError):
        parse_structured("not json at all", TriageResult)


def test_parse_structured_raises_on_schema_violation():
    with pytest.raises(StructuredOutputError):
        parse_structured('{"severity": "major"}', TriageResult)  # missing required "category"
