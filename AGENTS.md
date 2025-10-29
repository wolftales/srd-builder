# AGENTS.md — SRD-Builder guardrails

## Workflow
- One feature per PR; never commit to main.
- Before commit: `pre-commit run -a` and `pytest -q`.
- Always ensure formatting and linting pass locally with `black .` and `ruff check src tests` prior to committing.
- Determinism: no timestamps/env-dependent values in dataset files.

## Boundaries
- parse_monsters.py: pure parsing/mapping only (no I/O/logging).
- postprocess.py: pure normalization/polish (legendary, CR, text, defenses, ids).
- indexer.py: pure index building.
- build.py: the only I/O orchestrator.
- validate.py: schema validation; no mutations.

## Data Shapes
- Target shapes = docs/templates/TEMPLATE_*.json.
- Fixtures split: tests/fixtures/.../raw vs .../normalized.
- Entities and nested entries must include `simple_name` where applicable.

## Style
- Python 3.11 + type hints.
- Ruff + Black must pass; import order via ruff/isort.
- No prints or side effects at import.
