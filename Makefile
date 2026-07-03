.PHONY: bootstrap check check-python check-web dev-server dev-web test test-python test-web

bootstrap:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'
	pnpm install

check: check-python check-web

check-python:
	.venv/bin/ruff check .
	.venv/bin/mypy

check-web:
	pnpm check

test: test-python test-web

test-python:
	.venv/bin/pytest

test-web:
	pnpm test

dev-server:
	.venv/bin/uvicorn embalming_server.main:app --app-dir apps/server --reload

dev-web:
	pnpm dev
