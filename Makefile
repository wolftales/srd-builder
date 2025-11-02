.PHONY: init lint test format pre-commit ci output bundle

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
	pytest -q -m "not package"

test-all:
	pytest -q

test-package:
	pytest -q -m package

pre-commit:
	pre-commit run --all-files

ci: lint test

output:
	python -m srd_builder.build --ruleset srd_5_1 --out dist

bundle:
	python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle
