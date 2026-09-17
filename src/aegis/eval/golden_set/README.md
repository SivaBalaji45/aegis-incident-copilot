# Golden set

`sample.json` is a 5-item starter set (illustrative, hand-written) showing the
shape the real golden set needs. Building the real one means pulling 75–150
historical incidents from the providers in `ingestion/providers.py` (their
status pages keep incident history, not just current incidents) and hand
labeling:

- `severity`, `category` — for the triage agent's classification metrics
- `relevant_chunk_ids` — which knowledge-base chunks should be retrieved,
  for Recall@k / MRR (requires the knowledge base to be populated first)
- `reference_summary` — a human-written root-cause summary, for ROUGE-L /
  faithfulness comparison against the diagnosis agent's output

This is genuinely a weekend or two of manual labeling, not something to
fabricate — a golden set with invented ground truth would defeat the point
of having one.
