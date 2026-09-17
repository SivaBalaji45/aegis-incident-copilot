.PHONY: install install-eval db-up db-init api dev-frontend test lint poll-once eval

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"

install-eval:
	.venv/bin/pip install -e ".[eval]"

db-up:
	docker compose up -d db

db-init:
	.venv/bin/python scripts/init_db.py

api:
	.venv/bin/uvicorn aegis.api.main:app --reload

dev-frontend:
	cd frontend && npm install && npm run dev

test:
	.venv/bin/pytest -q

lint:
	.venv/bin/ruff check src tests

poll-once:
	.venv/bin/python -m aegis.ingestion.poller

eval:
	.venv/bin/python -m aegis.eval.run_eval
