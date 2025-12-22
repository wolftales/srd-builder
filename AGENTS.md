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
- parse_*.py: pure parsing/mapping only (no I/O/logging).
- postprocess/: pure normalization/polish (legendary, CR, text, defenses, ids).
- indexer.py: pure index building.
- build.py: the only I/O orchestrator.
- validate.py: schema validation; no mutations.

## Architectural Patterns

### Two Dataset Processing Patterns Exist:

**Pattern 1: Parse + Postprocess (Legacy - monsters, spells, equipment)**
- Parse phase: Extract and structure data from PDF
- Postprocess phase: Normalize, clean, generate IDs, polish text
- Two separate modules required
- Example: `parse_monsters.py` (987 lines) + `postprocess/monsters.py` (375 lines)

**Pattern 2: All-in-One Parse (Preferred - magic_items, tables)**
- Parse phase does everything: extraction, structuring, normalization, ID generation
- No postprocess module needed
- Single module, cleaner architecture
- Example: `parse_magic_items.py` (325 lines), `parse_tables.py` (196 lines)

**Guideline:** New datasets should use Pattern 2 (all-in-one parse). Pattern 1 datasets are legacy and may be refactored in future versions.

## Design Philosophy
- **No backwards compatibility:** Prefer clean, well-designed code over legacy support.
- **No legacy code:** If refactoring, remove old approaches entirely.
- **Breaking changes acceptable:** Schema and output formats can change between versions.
- **Quality over compatibility:** Choose the right design, document breaking changes.

## Data Shapes
- Target shapes = docs/templates/TEMPLATE_*.json.
- Fixtures split: tests/fixtures/.../raw vs .../normalized.
- Entities and nested entries must include `simple_name` where applicable.

## Consistency Guidelines
- **Alphabetical ordering:** Dictionary keys in metadata should be alphabetically sorted (extraction_status, schemas, files).
- **Metadata accuracy:** meta.json must reflect actual build output, not design intent (use file existence checks).
- **Test failures over skips:** Tests should FAIL when expected data is missing, not SKIP (catches build issues immediately, except CI where PDF is unavailable).
- **Single source of truth:** PAGE_INDEX is authoritative for page ranges; meta.json tracks build outputs.
- **No duplication:** Use references/aliases instead of duplicating data across files.
- **Field ordering:** Maintain consistent field order in _meta blocks across all datasets.

## Testing Guidelines

### Golden Test Pattern (Fixture-Based)
- **Location:** `tests/test_golden_*.py` (one per dataset)
- **Purpose:** End-to-end validation that parsing produces consistent, deterministic output
- **Fixture structure:**
  - `tests/fixtures/srd_5_1/raw/{dataset}.json` - Raw extraction data (input to parser)
  - `tests/fixtures/srd_5_1/normalized/{dataset}.json` - Expected final output (golden reference)
- **Pattern:** Load raw fixture → parse (+ postprocess if legacy) → compare to normalized fixture
- **Benefits:**
  - No dependency on `dist/` directory (works in CI without PDF)
  - Uses committed fixtures (always available)
  - Tests entire pipeline in one assertion
  - Catches any regression in parsing or postprocessing logic

### Golden Test Examples

**All-in-one parse (preferred):**
```python
def test_magic_items_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/magic_items.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/magic_items.json")

    magic_items_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_magic_items({"items": magic_items_raw})

    document = {"_meta": meta_block(...), "items": parsed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
```

**Parse + postprocess (legacy):**
```python
def test_monster_dataset_matches_normalized_fixture() -> None:
    raw_path = Path("tests/fixtures/srd_5_1/raw/monsters.json")
    expected_path = Path("tests/fixtures/srd_5_1/normalized/monsters.json")

    monsters_raw = json.loads(raw_path.read_text(encoding="utf-8"))
    parsed = parse_monster_records(monsters_raw)
    processed = [clean_monster_record(monster) for monster in parsed]

    document = {"_meta": meta_block(...), "items": processed}

    rendered = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    expected = expected_path.read_text(encoding="utf-8")
    assert rendered == expected
```

### Fixture Maintenance
- Keep fixtures small (5-10 representative items, not entire datasets)
- Update fixtures when parser output format changes (expected breakage)
- Fixtures are NOT for backwards compatibility - they validate current behavior
- Regenerate fixtures from actual build output when making intentional changes

## Style
- Python 3.11 + type hints.
- Ruff (linting + formatting) must pass; import order enforced by ruff.
- No prints or side effects at import.
