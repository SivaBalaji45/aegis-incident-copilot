"""Live eval harness: runs the triage agent against the golden set and reports
classification metrics. This is the piece that's cheap enough (one "fast"-tier
call per incident, no DB required) to run as a fast per-PR CI gate once
ANTHROPIC_API_KEY is available in CI; retrieval/diagnosis/critic metrics need
a populated knowledge base and are intended for a nightly run against the
full golden set instead (see README's LLMOps section).

Usage: python -m aegis.eval.run_eval [--threshold 0.7]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from aegis.agents.prompts import TRIAGE_SYSTEM
from aegis.eval.metrics import precision_recall_f1
from aegis.guardrails.schemas import TriageResult
from aegis.llm.parsing import parse_structured
from aegis.llm.router import generate

GOLDEN_SET_PATH = Path(__file__).parent / "golden_set" / "sample.json"


async def _predict_severity(item: dict) -> str:
    prompt = f"Title: {item['title']}\n\nBody:\n{item['body_text']}"
    raw = await generate("fast", TRIAGE_SYSTEM, prompt, max_tokens=512)
    result = parse_structured(raw, TriageResult)
    assert isinstance(result, TriageResult)
    return result.severity


async def run(golden_set_path: Path) -> dict[str, float]:
    items = json.loads(golden_set_path.read_text())
    predicted = await asyncio.gather(*(_predict_severity(item) for item in items))
    gold = [item["severity"] for item in items]
    return precision_recall_f1(list(predicted), gold)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.6)
    parser.add_argument("--golden-set", type=Path, default=GOLDEN_SET_PATH)
    args = parser.parse_args()

    scores = asyncio.run(run(args.golden_set))
    print(json.dumps(scores, indent=2))

    if scores["f1"] < args.threshold:
        print(f"FAIL: triage F1 {scores['f1']:.3f} below threshold {args.threshold}", file=sys.stderr)
        sys.exit(1)
    print("PASS")


if __name__ == "__main__":
    main()
