.PHONY: init lint test format pre-commit ci

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

pre-commit:
	pre-commit run --all-files

ci: lint test
