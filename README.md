# Aegis Incident Copilot

A multi-agent incident-intelligence system that polls public status-page APIs
(GitHub, Cloudflare, Stripe, Datadog, PagerDuty, Twilio, AWS, GCP, and more),
triages new incidents, retrieves grounded evidence from a knowledge base of
postmortems and runbooks, drafts a cited root-cause hypothesis, and runs that
hypothesis back through a **critic agent** that checks every claim against
the retrieved evidence before anything reaches a human for approval.

Nothing external ever auto-publishes. A human approves the draft first —
that's not a limitation, it's the right architecture for an agent operating
near customer communications.

## Architecture

```
Public status APIs (GitHub, Cloudflare, Stripe, Datadog, AWS, GCP...)
        |
        v
Ingestion & normalization  (APScheduler poller -> Postgres)
        |
        v
Incident store (Postgres)  +  RAG knowledge base (pgvector: postmortems, runbooks)
        |
        v
Multi-agent orchestration (LangGraph)
  Triage -> Retrieve+Rerank -> Diagnosis -> Critic --ungrounded, retries left--> (back to Retrieve)
                                               |
                                          grounded
                                               v
                                            Draft
        |
        v
FastAPI + React dashboard -- human approves before anything external publishes
```

The agent pipeline (`src/aegis/agents/graph.py`) is a LangGraph **state
machine**, not a linear chain: the critic node can route back to retrieval
with a refined query. That loop is capped at `AEGIS_MAX_CRITIC_RETRIES` (default
2) — past that, the incident is flagged `needs_human_review` instead of
looping forever or shipping an ungrounded answer.

## What's real vs. scaffolded right now

This repo was bootstrapped as a working skeleton, not a finished product.
Honest status:

| Piece | Status |
|---|---|
| Status-page ingestion (fetch, normalize, dedupe) | **Working** — verified live against GitHub's and Cloudflare's real APIs |
| DB models / schema (Postgres + pgvector) | Written, not yet run against a live database in this environment (no local Postgres/Docker available where this was scaffolded) |
| LangGraph pipeline wiring (triage → retrieval → diagnosis → critic → draft, with the critic retry loop) | **Compiles and routes correctly** (unit-tested); the LLM calls themselves need `ANTHROPIC_API_KEY` and a populated knowledge base to run end-to-end |
| FastAPI backend + review endpoints | **Working** — verified with FastAPI's TestClient |
| React dashboard | **Working** — verified rendering against a live (unreachable-DB) backend; needs a real Postgres + populated incidents to show real data |
| Eval harness metrics (Recall@k, MRR, F1, ROUGE-L) | **Working**, unit-tested |
| Eval harness golden set | 5 illustrative examples only — see `src/aegis/eval/golden_set/README.md` for what building the real 75–150-incident set requires |
| Multimodal doc ingestion (Document QA, Visual Document Retrieval) | Interfaces defined in `src/aegis/rag/doc_ingest.py`, not implemented — text-only RAG path is complete and usable today |
| Langfuse/Phoenix tracing, semantic cache, Celery scale-out | Not yet wired in — see Roadmap |

## Setup

### 1. Backend

```bash
make install          # creates .venv, installs the package + dev deps
cp .env.example .env  # fill in ANTHROPIC_API_KEY at minimum
```

Bring up Postgres with pgvector (requires Docker):

```bash
make db-up
make db-init
```

Run the API (also starts the ingestion scheduler):

```bash
make api
```

Poll once by hand, without waiting for the scheduler:

```bash
make poll-once
```

### 2. Frontend

```bash
make dev-frontend     # npm install + vite dev server on :5173, proxies /api -> :8000
```

### 3. Tests / lint

```bash
make test
make lint
```

23 unit tests cover ingestion normalization, chunking, eval metrics, PII
redaction, structured-output parsing, and the critic's retry-routing logic —
all pure/deterministic, no network or DB required. This is the subset wired
into `.github/workflows/ci.yml` as a merge-blocking regression gate.

### 4. Populating the knowledge base

`src/aegis/rag/chunking.py` + `embeddings.py` handle plain-text postmortems/
runbooks end-to-end (chunk → embed → store in `knowledge_chunks`). There's no
bulk-loader CLI yet — see Roadmap.

## HuggingFace task mapping

| Task | Where |
|---|---|
| Zero-Shot Classification + Token Classification (NER) | `agents/triage.py` — implemented as one structured-output LLM call rather than two separate HF pipelines (see that file's docstring for the tradeoff) |
| Feature Extraction / Sentence Similarity | `rag/embeddings.py` (`sentence-transformers`, `bge-small-en-v1.5` by default) |
| Text Ranking | `rag/reranker.py` (cross-encoder rerank of the top-k vector-search candidates) |
| Document Question Answering (multimodal) | `rag/doc_ingest.py::answer_from_page` — interface defined, not implemented |
| Visual Document Retrieval (multimodal) | `rag/doc_ingest.py::embed_page_images` — interface defined, not implemented |
| Summarization | `agents/prompts.py::DRAFT_SYSTEM` (condenses diagnosis + citations into a status update) |
| Text Generation | `agents/diagnosis.py`, `agents/critic.py`, `agents/drafting.py` |

## Guardrails

- Every agent's LLM output is parsed into a Pydantic schema (`guardrails/schemas.py`)
  via `llm/parsing.py` — malformed output raises at the node boundary instead
  of propagating a half-shaped dict downstream.
- Ingested incident/postmortem text is treated as **evidence, not
  instructions** — the diagnosis prompt says so explicitly (`agents/prompts.py`),
  because pulling text from the open internet into an agent loop is a real
  prompt-injection surface.
- `guardrails/pii.py` does a first-pass regex redaction (email/IP/phone) on
  incident text before it's sent to any LLM.
- The human-approval gate (`POST /diagnoses/{id}/review`) is the only way a
  diagnosis's `status` moves to `approved` — nothing auto-publishes.

## Roadmap

- Bulk-loader CLI for postmortem/runbook ingestion into the knowledge base
- Wire the critic's groundedness check to RAGAS/DeepEval instead of a raw
  LLM-as-judge call, and extend `run_eval.py` to cover the full pipeline
  (currently triage-only, since that's the piece cheap enough for per-PR CI)
- Grow the golden set to 75–150 real, hand-labeled historical incidents
- Langfuse/Phoenix tracing on every agent node (input/output/latency/cost)
- Semantic cache for duplicate/near-duplicate incidents across providers
- Implement `rag/doc_ingest.py`'s multimodal path (PDF page rendering +
  ColPali-style visual retrieval + document QA) for postmortems where tables
  or architecture diagrams matter
- Celery + Redis if/when ingestion volume actually makes the in-process
  APScheduler + asyncio.gather setup a bottleneck — not before
