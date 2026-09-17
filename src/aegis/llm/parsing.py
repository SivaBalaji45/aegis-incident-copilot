"""Turns an LLM's raw text response into a validated Pydantic model. Every
agent node's output goes through this rather than a bare `json.loads`, so a
malformed response raises here — at the node boundary — instead of silently
becoming a partially-shaped dict on the graph state."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, ValidationError

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


class StructuredOutputError(ValueError):
    pass


def parse_structured(text: str, model: type[BaseModel]) -> BaseModel:
    fence_match = _FENCE_RE.search(text)
    payload = fence_match.group(1) if fence_match else text
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise StructuredOutputError(f"Could not parse JSON from LLM output: {exc}") from exc
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise StructuredOutputError(f"LLM output failed schema validation: {exc}") from exc
