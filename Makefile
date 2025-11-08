.PHONY: init lint test format pre-commit ci output bundle bump-version

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

tables:
	python -m srd_builder.build --ruleset srd_5_1 --out dist --tables-only --bundle

bump-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=0.6.5"; \
		exit 1; \
	fi
	python scripts/bump_version.py $(VERSION)
