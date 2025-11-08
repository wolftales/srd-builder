.PHONY: init lint test format pre-commit ci output bundle tables monsters equipment spells bump-version

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

monsters:
	python -m srd_builder.build --ruleset srd_5_1 --out dist --monsters-only --bundle

equipment:
	python -m srd_builder.build --ruleset srd_5_1 --out dist --equipment-only --bundle

spells:
	python -m srd_builder.build --ruleset srd_5_1 --out dist --spells-only --bundle

bump-version:
	@if [ -z "$(VERSION)" ]; then \
		echo "Usage: make bump-version VERSION=0.6.5"; \
		exit 1; \
	fi
	python scripts/bump_version.py $(VERSION)
