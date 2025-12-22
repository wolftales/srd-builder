# AGENTS.md — SRD-Builder guardrails

## Workflow
- **Branch:** one feature per PR. Never commit to main.
- **Local development:**
  - pre-commit run -a
  - pytest -q
- **CI and container environments (no pre-commit available):**
  - ruff check .
  - ruff format --check .
  - pytest -q
- Determinism: No timestamps or environment-dependent values in dataset files.


## Boundaries
- parse_monsters.py: pure parsing/mapping only (no I/O/logging).
- postprocess/: pure normalization/polish (legendary, CR, text, defenses, ids).
- indexer.py: pure index building.
- build.py: the only I/O orchestrator.
- validate.py: schema validation; no mutations.

## Design Philosophy
- **No backwards compatibility:** Prefer clean, well-designed code over legacy support.
- **No legacy code:** If refactoring, remove old approaches entirely.
- **Breaking changes acceptable:** Schema and output formats can change between versions.
- **Quality over compatibility:** Choose the right design, document breaking changes.

## Data Shapes
- Target shapes = docs/templates/TEMPLATE_*.json.
- Fixtures split: tests/fixtures/.../raw vs .../normalized.
- Entities and nested entries must include `simple_name` where applicable.

## Style
- Python 3.11 + type hints.
- Ruff (linting + formatting) must pass; import order enforced by ruff.
- No prints or side effects at import.
