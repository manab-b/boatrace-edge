install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

run:
	uvicorn boatrace_edge.api:app --reload

db-migrate:
	psql "$$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/001_foundation.sql
