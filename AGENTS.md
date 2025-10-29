# AGENTS.md — SRD-Builder guardrails

## Workflow
- Branch: one feature per PR. Never commit to main.
- Run locally before commit:
  - pre-commit run -a
  - pytest -q
- Run in CI or Codex containers (no pre-commit available):
  - ruff check
  - ruff format --check
  - black --check
  - pytest -q
- Determinism: No timestamps or environment-dependent values in dataset files.

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
