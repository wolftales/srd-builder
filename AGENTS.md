# AGENTS.md — SRD-Builder guardrails

## Workflow
- Branch: one feature per PR. Never commit to main.
- Run locally before commit:
  - pre-commit run -a
  - pytest -q
- Determinism: No timestamps or environment-dependent values in dataset files.

## Code Boundaries
- parse_monsters.py: pure field parsing/mapping only (no I/O, no logging).
- postprocess.py: pure normalization & polishing (legendary split, CR, text, defenses, ids).
- indexer.py: builds lookup maps from in-memory entities; no text cleanup.
- build.py: the only place that does I/O orchestration.
- validate.py: schema-only validation; do not mutate data.

## Data Shapes
- Target shapes = docs/templates/TEMPLATE_*.json.
- Raw fixtures live under tests/fixtures/.../raw; normalized expected outputs under .../normalized.
- All entities and nested entries must have `simple_name`.

## Style
- Python 3.10+, type hints required.
- Ruff + Black must pass; fix lint automatically (`ruff --fix`).
- No prints or side effects at import time.
- Keep imports minimal; remove unused symbols.

## Tests
- Unit tests for each pure function.
- Golden test: same input → identical bytes for `monsters.json` and `index.json`.
- If adding new parsers (spells/items/classes): include raw+normalized fixtures and schemas.
