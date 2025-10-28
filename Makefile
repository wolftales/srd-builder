.PHONY: init lint test format ci

init:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .
	black --check .
	isort --check-only .

format:
	ruff check --fix .
	black .
	isort .

test:
	pytest -q

ci: lint test
