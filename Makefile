.PHONY: init lint test format pre-commit ci verify-ci output bundle smoke release-check sync-docs tables monsters equipment spells bump-version

init:
	pip install -e ".[dev]"
	@# macOS: iCloud / Finder may flag site-packages as UF_HIDDEN, which
	@# causes Python 3.14's site.py to skip .pth files (including the
	@# editable install marker). Clear the flag so imports work.
	@if [ -d .venv ] && command -v chflags >/dev/null 2>&1; then \
		chflags -R nohidden .venv; \
	fi
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
	@echo "1/5 Checking formatting..."
	@ruff format --check . || (echo "❌ Format errors! Run: make format" && exit 1)
	@echo "2/5 Checking linting..."
	@ruff check . || (echo "❌ Lint errors! Run: ruff check . --fix" && exit 1)
	@echo "3/5 Checking doc-table sync..."
	@python scripts/sync_doc_tables.py --check || (echo "❌ Doc tables drifted! Run: make sync-docs" && exit 1)
	@echo "4/5 Running tests..."
	@pytest -q || (echo "❌ Test failures!" && exit 1)
	@echo "5/5 Validating shipped bundle against schemas (strict)..."
	@python -m srd_builder.utils.validate --ruleset srd_5_1 || (echo "❌ Bundle has schema violations! Inspect with: python -m srd_builder.utils.validate --ruleset srd_5_1 --report-only" && exit 1)
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
	@python scripts/sync_doc_tables.py
	@echo "✓ Bundle complete. Run 'make smoke MODE=bundle' to validate."

# Quick validation (item counts + optional bundle structure)
smoke:
	@./scripts/smoke.sh srd_5_1 dist $(MODE)

# Deterministic validation (hash comparison + item counts)
release-check:
	@./scripts/release_check.sh srd_5_1 dist

# Sync doc count/schema tables from dist/srd_5_1/meta.json (idempotent)
sync-docs:
	@python scripts/sync_doc_tables.py

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
