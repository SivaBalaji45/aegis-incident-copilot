"""Lightweight PII redaction on ingested text before it reaches any prompt.

Status-page incident text is public and provider-authored, but runbooks and
postmortems pulled into the knowledge base may be internal documents that
slipped in with emails, IPs, or phone numbers embedded. This is a regex-based
first pass, not a guarantee — the point is to strip the common, cheap cases
before anything is embedded or sent to an LLM.
"""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")


def redact(text: str) -> str:
    text = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = _IPV4_RE.sub("[REDACTED_IP]", text)
    text = _PHONE_RE.sub("[REDACTED_PHONE]", text)
    return text
