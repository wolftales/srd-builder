# srd-builder

[![CI](https://github.com/wolftales/srd-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/wolftales/srd-builder/actions/workflows/ci.yml)

A boring-by-design toolkit for rebuilding System Reference Document (SRD) rulebooks into
structured data. The repository focuses on reliable automation and validation pipelines so
you can reproduce datasets locally without shipping proprietary PDFs.

## Project scope

This project is a personal, reproducible SRD builder. It is **not** a dataset mirror. Future
iterations will support multiple rulesets (5.2.1, OGL/ORC material, Pathfinder) once the
scaffolding here is hardened.

## Getting started

```bash
git clone https://github.com/wolftales/srd-builder.git
cd srd-builder

# Create and activate a Python 3.14+ virtual environment
python3.14 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Editable install with dev extras
pip install -e ".[dev]"

# (Optional) Place the CC-BY SRD PDF at rulesets/srd_5_1/SRD_CC_v5.1.pdf
# to enable PDF-extracted datasets (monsters, spells, equipment, magic_items).

# Build the full bundle: data + schemas + docs + bundle README
make bundle
```

Output lands in [dist/srd_5_1/](dist/srd_5_1/). Use it from Python:

```python
import json
from pathlib import Path

monsters = json.loads(Path("dist/srd_5_1/monsters.json").read_text())
print(f"{len(monsters['items'])} monsters, schema {monsters['_meta']['schema_version']}")
```

Without a PDF, the static datasets still build (classes, lineages, conditions, skills, etc.);
PDF-extracted datasets (monsters, spells, equipment, magic_items) come back empty. The
`raw/` subdirectory under `rulesets/srd_5_1/` is for build-generated `*_raw.json`
intermediates, not the PDF.

See [Build & validate](#build--validate) below for variations (data-only build, smoke checks,
release verification).

## Datasets

Latest build: **1,695 items across 16 datasets** (counts and schema versions are written to
`dist/srd_5_1/meta.json` on every build).

| Dataset | Count | Schema |
|---|---:|---|
| Monsters | 317 | 2.0.0 |
| Spells | 319 | 2.0.0 |
| Equipment | 259 | 2.1.0 |
| Magic Items | 240 | 2.0.0 |
| Features | 245 | 3.0.0 |
| Rules | 172 | 2.0.0 |
| Tables | 38 | 2.0.0 |
| Skills | 18 | 1.0.0 |
| Conditions | 15 | 2.0.0 |
| Poisons | 14 | 2.0.0 |
| Damage Types | 13 | 1.0.0 |
| Lineages | 13 | 2.0.0 |
| Classes | 12 | 2.1.0 |
| Weapon Properties | 11 | 1.0.0 |
| Ability Scores | 6 | 1.0.0 |
| Diseases | 3 | 2.0.0 |

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full pipeline and schema-evolution
policy.

## Build & validate

**Build commands:**

```bash
make bundle             # Full bundle: data + schemas + docs + bundle README (default for releases)
make build              # Data-only: 16 JSON files + index.json + meta.json (faster, dev iteration)

# Or directly:
PYTHONPATH=src python -m srd_builder.build --ruleset srd_5_1 --out dist           # data only
PYTHONPATH=src python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle  # full bundle
```

**Bundle output (`make bundle`):**

```
dist/srd_5_1/
├── ability_scores.json    # 6
├── classes.json           # 12
├── conditions.json        # 15
├── damage_types.json      # 13
├── diseases.json          # 3
├── equipment.json         # 259
├── features.json          # 245
├── lineages.json          # 13
├── magic_items.json       # 240
├── monsters.json          # 317
├── poisons.json           # 14
├── rules.json             # 172
├── skills.json            # 18
├── spells.json            # 319
├── tables.json            # 38
├── weapon_properties.json # 11
├── index.json             # Cross-dataset lookup with aliases
├── meta.json              # Versions, license, inventory, schema map
├── build_report.json      # Build provenance (timestamp, builder version, sources)
├── quality_report.json    # Audit findings from scripts/quality_report.py
├── README.md              # Auto-generated consumer-facing README
├── schemas/               # 16 schemas + schemas/exemplars/ (one valid instance each)
└── docs/                  # SCHEMAS.md, DATA_DICTIONARY.md
```

`make build` produces the same JSON files but skips `schemas/`, `docs/`, the bundle README,
and the schema exemplars.

**Pipeline (per-dataset):**

1. **Extract** — `src/srd_builder/extract/` (per-dataset PDF extractors) and
   `src/srd_builder/extraction/` (the table-extraction engine: `extractor.py`, `patterns.py`,
   `extraction_metadata.py`). PDF-text primitives live in
   [src/srd_builder/utils/pdf_probe.py](src/srd_builder/utils/pdf_probe.py).
2. **Parse** — `src/srd_builder/parse/parse_<dataset>.py` maps raw text into typed records.
3. **Postprocess** — `src/srd_builder/postprocess/engine.py` drives `DATASET_CONFIGS` for
   normalization (whitespace, ID stamping, sorting, alias resolution).
4. **Assemble** — `src/srd_builder/assemble/` builds the cross-dataset `index.json`.
5. **Validate** — `src/srd_builder/validate.py` runs every dataset against its JSON Schema
   (`schemas/<dataset>.schema.json`) using `Draft202012Validator`.

**Validation & smoke checks:**

```bash
make smoke              # Item counts + meta.json structure (data-only build)
make smoke MODE=bundle  # + schemas/, docs/, bundle README, exemplars present
make release-check      # Determinism: full rebuild + hash compare + counts
PYTHONPATH=src python -m srd_builder.validate --ruleset srd_5_1   # Full schema validation
```

See [docs/VERIFICATION_CHECKLIST.md](docs/VERIFICATION_CHECKLIST.md) for the full release
checklist.

## Determinism

Same inputs → same bytes. Arrays are sorted where order isn't meaningful, and dataset files
contain no timestamps; only `build_report.json` records build time. `make release-check`
rebuilds twice and diffs the hashes.

## Identifier policy

Every dataset entry exposes both `id` and `simple_name`. Identifiers are lowercase ASCII
snake_case matching `[a-z0-9_]+`. Top-level IDs carry a dataset prefix (e.g. `monster:`,
`spell:`, `feature:<owner>:<name>` as of v0.25.0). Cross-references between datasets always
use IDs, never display names.

## Use cases

- **VTT integrations** — Roll20, Foundry VTT, Fantasy Grounds
- **Companion apps** — character sheets, monster reference, DM tools
- **AI / LLM tooling** — D&D chatbots, rule assistants, content generation
- **Campaign tools** — encounter builders, initiative trackers
- **Analysis & research** — game balance studies, statistical modeling

Consumer-side validation example:

```python
import json
from jsonschema import Draft202012Validator

schema = json.load(open("dist/srd_5_1/schemas/monster.schema.json"))
data = json.load(open("dist/srd_5_1/monsters.json"))

validator = Draft202012Validator(schema)
for error in validator.iter_errors(data["items"][0]):
    print(error.message)
```

## Development

```bash
make pre-commit    # Run all pre-commit hooks
make lint          # ruff format + ruff check
make test          # pytest -q
make ci            # Full CI simulation (lint + test)
```

Direct commands when `make` isn't available (CI / containers):

```bash
ruff check .
ruff format --check .
pytest -q
```

**Tests:** 294 passing, 19 skipped (skips are dataset-specific gates that wait on a PDF
when none is committed). Golden tests live in `tests/test_golden_<dataset>.py` and pin
parse + postprocess output against fixtures under `tests/fixtures/srd_5_1/`. PDF-extraction
provenance reproducer tests live in
[tests/test_pdf_provenance.py](tests/test_pdf_provenance.py); see
[AGENTS.md § PDF extraction discipline](AGENTS.md) for the rules around adding more.

## Versioning

srd-builder uses two version numbers:

- **Package version** (currently `v0.27.7`, read from `pyproject.toml` at runtime via
  `importlib.metadata`) — the builder release.
- **Schema version** — each dataset schema in `schemas/*.schema.json` evolves independently
  (currently `1.0.0`–`3.0.0`). Schema versions are written into `dist/srd_5_1/meta.json`
  and each dataset's `_meta.schema_version`.

Bump the package version with:

```bash
python scripts/bump_version.py 0.27.6          # commit + tag locally
python scripts/bump_version.py 0.27.6 --no-commit   # preview only
```

See [docs/ARCHITECTURE.md § Version Management](docs/ARCHITECTURE.md) for the policy.

## Repository layout

```text
srd-builder/
├── src/srd_builder/
│   ├── build.py                  # CLI orchestrator (--ruleset, --out, --bundle)
│   ├── validate.py               # JSON Schema validation
│   ├── validate_references.py    # Cross-dataset reference auditor
│   ├── constants.py              # Versioned/static builder constants
│   ├── extract/                  # Table engine + bespoke per-dataset extractors
│   │   ├── extractor.py          # Table-extraction engine
│   │   ├── patterns.py           # Table-extraction patterns
│   │   ├── table_targets.py      # Hand-curated table targets
│   │   └── datasets/             # Per-dataset PDF extractors (extract_*.py)
│   ├── parse/                    # parse_<dataset>.py
│   ├── postprocess/              # engine.py + DATASET_CONFIGS
│   ├── assemble/                 # Cross-dataset indexer
│   ├── rulesets/srd_5_1/         # Per-ruleset hand-curated Python data (class/lineage/spell targets)
│   └── utils/                    # pdf_probe, page_index, metadata, prose, helpers
├── rulesets/
│   └── srd_5_1/
│       ├── SRD_CC_v5.1.pdf       # (gitignored) Source PDF
│       └── raw/                  # (gitignored) Build-generated *_raw.json intermediates
├── schemas/                      # 16 JSON Schema definitions (source of truth)
├── tests/
│   ├── fixtures/srd_5_1/         # Raw + normalized golden fixtures
│   ├── test_golden_*.py          # End-to-end pipeline pins (one per dataset)
│   ├── test_pdf_provenance.py    # PDF-extractability reproducer tests
│   └── ...                       # ~80 unit + integration test files
├── docs/                         # ARCHITECTURE, ROADMAP, BACKLOG, PROVENANCE, etc.
├── scripts/                      # bump_version, smoke, quality_report, release_check
├── archive/                      # Historical snapshots + retired code
├── dist/                         # (gitignored) Build output
├── .github/workflows/ci.yml
├── AGENTS.md                     # Agent behavior guidelines
├── Makefile
├── pyproject.toml
└── .pre-commit-config.yaml
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full history. **Latest release: v0.27.7** — `equipment_extended.py` provenance hardening (BACKLOG proposal 2): the last remaining hand-curated equipment module had each record's free-text `_note` field replaced with a typed `_provenance` block (`source`, `reason`, `referenced_by`, `module`, `estimates`). New `ExtendedProvenance` TypedDict pins the shape statically; new `_provenance` property on `equipment.schema.json` (bumped 2.1.0 → 2.2.0) pins it at the JSON layer; new `tests/test_equipment_extended_provenance.py` (5 tests) pins it at runtime including the 8-vs-1 split between pack and monster cross-references. The previous `_note` field was silently violating the schema's `additionalProperties: false`; downstream consumers can now programmatically filter inferred records instead of grepping prose. Closes the last open follow-up in PROVENANCE / BACKLOG; the v0.27.x line is now complete.

Key milestones:

- **v0.3.0–v0.7.x** — PDF extraction + structured field parsing
- **v0.9.x** — Equipment + reference tables + class progressions
- **v0.14.0** — Conditions, diseases, madness, poisons (deterministic prose pipeline)
- **v0.15.0** — Module reorganization + monster/spell refactor
- **v0.16.0** — Magic items dataset (240 items)
- **v0.17.0** — Rules dataset (172 rules, 7 chapters)
- **v0.18.0–v0.21.0** — Modular refactor, postprocess engine, cross-reference validation
- **v0.22.x** — Editable install + macOS `UF_HIDDEN` fixes; dynamic package version
- **v0.27.7** — `equipment_extended.py` provenance hardening (BACKLOG proposal 2): free-text `_note` replaced by typed `_provenance` block (`source`, `reason`, `referenced_by`, `module`, `estimates`); `ExtendedProvenance` TypedDict + `equipment.schema.json` 2.2.0 `_provenance` property + 5-test pin in `tests/test_equipment_extended_provenance.py`; the previous `_note` field was silently violating `additionalProperties: false`; closes the last open follow-up in PROVENANCE / BACKLOG; v0.27.x line complete; 563 passed
- **v0.27.6** — `equipment_descriptions.py` retired (P7 cutover): 398-line `*_DESCRIPTIONS` literals replaced by live `extract_equipment_descriptions.py`; section-aware concatenation + Title-Case heading regex with lowercase-glue alternation + 69-entry dispatch table + subsection-terminator slicing yield 69-for-69 recovery; surfaced 6 silently-stripped description phrases and 2 incorrect curated `page` fields as drift in the retired literal; `assemble_equipment_from_tables` takes `equipment_descriptions=` kwarg; v0.27.x retirement line totals ~2,856 lines deleted across 6 modules; PROVENANCE 3 → 1 active; 558 passed (73 new assertions)
- **v0.27.5** — `equipment_packs.py` retired (P6 cutover): 323-line `EQUIPMENT_PACKS` literal replaced by live `extract_equipment_packs.py`; pack-header regex + `_PHRASE_TO_ITEM` resolution table + trailing-rope sentence handling yield 7-for-7 byte-perfect parity (name, cost_gp, description, contents); curly-apostrophe normalized to ASCII at output; `assemble_equipment_from_tables` takes `equipment_packs=` kwarg; closes v0.27.x retirement line at ~2,458 lines deleted; PROVENANCE 4 → 3 active; 485 passed
- **v0.27.4** — Equipment page-constants drift fixed + cross-extractor audit: `EQUIPMENT_START_PAGE` / `EQUIPMENT_END_PAGE` harmonized from 0-indexed `61`–`72` to 1-indexed `62`–`74` (matching `PAGE_INDEX["equipment"]`); 8 silently-dropped rows from PDF page 74 (Services / Lifestyle tables) now extracted; new parametrized audit test `test_extractor_page_constants_agree_with_page_index` pins all 4 per-dataset extractors against canonical `PAGE_INDEX`; +4 new test assertions (464 passed)
- **v0.27.3** — `poison_descriptions.py` retired (P4 cutover): 129-line hand-curated `POISON_DESCRIPTIONS` replaced by live `parse_poison_descriptions.py`; damage regex extended to `tak(?:es?|ing)` unblocks 4 delayed-damage poisons; description header strip + `type_id` emit yield 14/14 byte-perfect parity; PROVENANCE shrinks 5 → 4; v0.27.x line concludes at ~2,135 lines deleted
- **v0.27.2** — `class_targets.py` retired (P3 cutover): five-step `extract_classes.py` replaces the 763-line hand-curated `CLASS_DATA`; `parse_classes()` / `parse_features()` take `class_data=` kwargs; bbox-aware progression walk handles newspaper layouts + duplicate columns + apostrophe/hyphen heals; 4 genuinely-unextractable cells reproducer-pinned
- **v0.27.1** — Prose section splitter fix + poison probe: `clean_text` smart-quote substitution repaired (was source-mangled no-op); `split_by_known_headers` gained `start_marker=` to skip preamble tables; `malice`/`torpor` no longer absorb ~2000/~3700 extra chars; `"Assassin's Blood"` restored to poison `known_headers`; dead U+2019 key in `POISON_DESCRIPTIONS` renamed; live poison extractor now returns clean 14/14; 4th "PDF corruption" claim disproven with reproducer
- **v0.27.0** — Hand-curated data retirement: `lineage_targets.py` (326 lines) replaced by live `extract_lineages.py` (P1); `spell_class_targets.py` (917 lines, byte-perfect 778-for-778 parity) replaced by `extract_spell_classes.py` (P2); `class_targets.py` reproducer added — text fully extractable, **DISPUTED** in PROVENANCE, retirement deferred (richer structural payload) (P3); `clean_spell_record()` now takes explicit `spell_classes_map=` kwarg; ~1,244 lines of hand-curated data deleted; +62 new test assertions
- **v0.26.2** — Structural cleanup of attempt #2: `extraction/` → `extract/` (table engine + bespoke extractors unified); hand-curated ruleset Python data consolidated under `src/srd_builder/rulesets/srd_5_1/`; shared prose utilities moved to `utils/prose.py`; workspace dirname literals swept into constants; `RULESETS` registry introduced (replaces lone `DATA_SOURCE`); `ruleset` parameter threaded through every parser/assembler/extractor; `source` field normalized to canonical `"SRD_CC_v5.1"` (was `"SRD 5.1"`); `stamp_source()` helper centralizes source stamping; `bump_version.py` fixed to thread `ruleset` through fixture regen
- **v0.26.1** — `utils/pdf_probe.py` shared PDF text-probe primitive (`open_pdf`, `page_text`, `normalize_whitespace`, `srd_page_to_pdf_index`); second reproducer test for spell-class lists pp. 105–113 (`SPELL_CLASSES` corruption claim DISPROVEN); BACKLOG ticket for v0.26.2 structural cleanup of `extract/` vs `extraction/` and ruleset-data home
- **v0.26.0** — Generated schema exemplars in bundle (one per schema, replaces `docs/templates/`); `docs/PROVENANCE.md` registry of hand-curated data sources with reason codes; `tests/test_pdf_provenance.py` reproducer test framework (first finding: lineage "PDF corrupted" claim is FALSE under pymupdf 1.27.x); dead `extraction/reference_data.py` removed (−625 net lines)
- **v0.25.0** — Owner-qualified feature IDs (`feature:{owner_simple_name}:{name}` + `owner_id` field); equipment IDs normalized through `normalize_id` (no more hyphens); audit clean on cross-refs + bad-id-format
- **v0.24.0** — Data-quality audit script; footer/control-char/damage-type fixes; `meta.json.datasets` block collapses files/inventory/extraction_status
- **v0.23.0** — Bundle README auto-generation, full schema coverage, inventory manifest, repo cleanup
- **v1.0.0** — Frozen schema + stable consumer API 🚀

## License

Code is MIT licensed (see [LICENSE](LICENSE)). Generated datasets inherit the license of the
source documents (e.g. CC-BY 4.0 for Wizards of the Coast SRDs); document attribution in any
outputs you share.
