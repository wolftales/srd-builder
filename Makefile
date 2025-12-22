.PHONY: init lint test format pre-commit ci verify-ci output bundle smoke release-check tables monsters equipment spells bump-version

init:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .

test:
	pytest -q -m "not package"

test-all:
	pytest -q

test-package:
	pytest -q -m package

pre-commit:
	pre-commit run --all-files

ci: lint test

# Verify CI will pass (run before pushing)
verify-ci:
	@echo "🔍 Verifying CI checks..."
	@echo "1/3 Checking formatting..."
	@ruff format --check . || (echo "❌ Format errors! Run: make format" && exit 1)
	@echo "2/3 Checking linting..."
	@ruff check . || (echo "❌ Lint errors! Run: ruff check . --fix" && exit 1)
	@echo "3/3 Running tests..."
	@pytest -q || (echo "❌ Test failures!" && exit 1)
	@echo "✅ All CI checks passed! Safe to push."

# Development build (data only, fast)
output:
	@echo "Building data files only..."
	python -m srd_builder.build --ruleset srd_5_1 --out dist
	@echo "✓ Build complete. Run 'make smoke' to validate."

# Production build (complete bundle)
bundle:
	@echo "Building complete bundle..."
	python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle
	@echo "✓ Bundle complete. Run 'make smoke MODE=bundle' to validate."

# Quick validation (item counts + optional bundle structure)
smoke:
	@./scripts/smoke.sh srd_5_1 dist $(MODE)

# Deterministic validation (hash comparison + item counts)
release-check:
	@./scripts/release_check.sh srd_5_1 dist

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
