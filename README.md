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

<!-- AUTO-SYNC:readme:totals-prefix START -->
Latest build: **1,687 items across 16 datasets** (counts and schema versions are written to
`dist/srd_5_1/meta.json` on every build).
<!-- AUTO-SYNC:readme:totals-prefix END -->

<!-- AUTO-SYNC:readme:dataset-table START -->
| Dataset | Count | Schema |
|---|---:|---|
| Spells | 319 | 2.0.0 |
| Monsters | 317 | 2.0.0 |
| Equipment | 259 | 2.2.0 |
| Features | 245 | 4.0.0 |
| Magic Items | 240 | 2.0.0 |
| Rules | 167 | 3.0.0 |
| Tables | 35 | 3.0.0 |
| Skills | 18 | 1.0.0 |
| Conditions | 15 | 3.0.0 |
| Poisons | 14 | 2.0.0 |
| Damage Types | 13 | 1.0.0 |
| Lineages | 13 | 2.0.0 |
| Classes | 12 | 2.1.0 |
| Weapon Properties | 11 | 1.0.0 |
| Ability Scores | 6 | 1.0.0 |
| Diseases | 3 | 3.0.0 |
<!-- AUTO-SYNC:readme:dataset-table END -->

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

<!-- AUTO-SYNC:readme:bundle-tree START -->
```
dist/srd_5_1/
├── ability_scores.json     # 6
├── classes.json            # 12
├── conditions.json         # 15
├── damage_types.json       # 13
├── diseases.json           # 3
├── equipment.json          # 259
├── features.json           # 245
├── lineages.json           # 13
├── magic_items.json        # 240
├── monsters.json           # 317
├── poisons.json            # 14
├── rules.json              # 167
├── skills.json             # 18
├── spells.json             # 319
├── tables.json             # 35
├── weapon_properties.json  # 11
├── index.json             # Cross-dataset lookup with aliases
├── meta.json              # Versions, license, inventory, schema map
├── build_report.json      # Build provenance (timestamp, builder version, sources)
├── quality_report.json    # Audit findings from scripts/quality_report.py
├── README.md              # Auto-generated consumer-facing README
├── schemas/               # 16 schemas + schemas/exemplars/ (one valid instance each)
└── docs/                  # SCHEMAS.md, DATA_DICTIONARY.md
```
<!-- AUTO-SYNC:readme:bundle-tree END -->

`make build` produces the same JSON files but skips `schemas/`, `docs/`, the bundle README,
and the schema exemplars.

**Pipeline (per-dataset):**

1. **Extract** — `src/srd_builder/extract/` hosts both layers: the config-driven
   table-extraction engine ([engine.py](src/srd_builder/extract/engine.py),
   [patterns/](src/srd_builder/extract/patterns/) package, one module per pattern
   type; [extraction_metadata.py](src/srd_builder/extract/extraction_metadata.py))
   and the per-dataset PDF extractors under
   [extract/datasets/](src/srd_builder/extract/datasets/). Reusable PDF primitives
   live in [utils/pdf_probe.py](src/srd_builder/utils/pdf_probe.py) (text/dict
   helpers) and [utils/pdf_layout.py](src/srd_builder/utils/pdf_layout.py)
   (column-aware span extraction + bbox math).
2. **Parse** — `src/srd_builder/parse/parse_<dataset>.py` maps raw text into typed records.
3. **Postprocess** — `src/srd_builder/postprocess/engine.py` drives `DATASET_CONFIGS`
   (in `configs.py`) to normalize 12 of the 16 datasets declaratively (id stamping,
   whitespace polish, nested-field cleaning). The 4 remaining datasets — monsters,
   spells, equipment, rules — keep custom per-record cleaners because they carry
   real domain logic or take extra kwargs the engine cannot model.
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

**Tests:** 690 passing. Golden tests live in `tests/test_golden_<dataset>.py` and pin
parse + postprocess output against fixtures under `tests/fixtures/srd_5_1/`. PDF-extraction
provenance reproducer tests live in
[tests/test_pdf_provenance.py](tests/test_pdf_provenance.py); see
[AGENTS.md § PDF extraction discipline](AGENTS.md) for the rules around adding more.

## Versioning

srd-builder uses two version numbers:

- **Package version** (currently `v0.37.1`, read from `pyproject.toml` at runtime via
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
│   │   ├── engine.py             # Config-driven table-extraction engine
│   │   ├── patterns/             # One module per pattern type (9 engines + _shared)
│   │   ├── extraction_metadata.py # TABLES config registry
│   │   ├── table_targets.py      # Hand-curated table targets
│   │   ├── text_parser_utils.py  # Word/Y-grouping helpers for text_region patterns
│   │   └── datasets/             # Per-dataset PDF extractors (extract_*.py)
│   ├── parse/                    # parse_<dataset>.py
│   ├── postprocess/              # engine.py + DATASET_CONFIGS (12 datasets) + 4 custom modules
│   ├── assemble/                 # Cross-dataset indexer
│   ├── rulesets/srd_5_1/         # Per-ruleset hand-curated Python data (class/lineage/spell targets)
│   └── utils/                    # pdf_probe, pdf_layout, page_index, metadata, prose, helpers
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

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full history.

Key milestones:
- **v0.1.0** — Foundation (infrastructure & tooling)
- **v0.2.0** — End-to-End Pipeline (fixture-based validation)
- **v0.3.0–v0.7.x** — PDF extraction + structured field parsing
- **v0.9.x** — Equipment + reference tables + class progressions
- **v0.14.0** — Conditions, diseases, madness, poisons (deterministic prose pipeline)
- **v0.15.0** — Module reorganization + monster/spell refactor
- **v0.16.0** — Magic items dataset (240 items)
- **v0.17.0** — Rules dataset (172 rules, 7 chapters)
- **v0.18.0–v0.21.0** — Modular refactor, postprocess engine, cross-reference validation
- **v0.22.x** — Editable install fixes; dynamic package version
- **v0.23.0** — Bundle README auto-generation, schema coverage, inventory manifest
- **v0.24.0** — Data-quality audit; footer/control-char/damage-type fixes
- **v0.25.0** — Owner-qualified feature IDs; normalized equipment IDs
- **v0.26.x** — Schema exemplars in bundle; PROVENANCE registry; PDF reproducer framework; `extract/` consolidation
- **v0.27.x** — Hand-curated data retirement (lineages, spell-class lists, classes, poisons, equipment packs/descriptions); provenance hardening
- **v0.28.0** — Data-integrity foundation (exemplar CI gate, known-truths gate, hyphenation fixes, round-trip page audit)
- **v0.28.1** — Table id naming consistency (`table:adventuring_gear`)
- **v0.29.0** — Postprocess engine consolidation: 12 datasets migrated to config-driven engine; 4 keep custom cleaners
- **v0.29.1** — Cross-stage naming consistency: `extract/extractor.py` renamed to `extract/engine.py`
- **v0.29.2** — Assembly code-path unification: 14 of 16 datasets share one write path; 2 prose datasets keep their richer `_meta` path
- **v0.29.3** — `_meta` block normalization + multi-system extensibility seams: all 16 datasets share the same enriched `_meta` (adds `game_system`, `dataset`, `source_pages`, `description`, `pdf_sha256`, `item_count`, `extraction_warnings`); `RULESETS` gains `game_system` + optional `id_prefix` so a future Pathfinder/Cypher ruleset can be added additively
- **v0.30.0** — Schema-consistency sweep (single Blackmoor migration window, breaking): `features.json`/`conditions.json`/`diseases.json` flip from per-dataset top-level keys to the canonical `{"items": [...]}` envelope; legacy `{key}_count` aliases dropped from `_meta`; all 19 rule duplicate IDs resolved via section-namespacing (`rule:{section}/{name}`) + collection-level dedupe; 3 appendix-duplicate tables (`lifestyle_expenses`, `food_drink_lodging`, `services`) suppressed; `assemble_prose_dataset` collapsed onto the single write path; audit goes 22 critical → 0 (0 critical / 0 warning / 0 info)
- **v0.31.0** — `extract_pdf_metadata.py` switched from raw `fitz.open()` to `pdf_probe.open_pdf()` + `page_text()`; output byte-identical. Small structural win; did NOT advance engine binding.
- **v0.32.0** — `extract_rules.py` switched to `pdf_probe.open_pdf()` + new `pdf_probe.page_dict()` helper (font/bbox/span metadata). Output byte-identical (3086 span blocks unchanged). The `page_dict()` helper is a genuine shared primitive; did NOT advance engine binding.
- **v0.33.0–v0.37.0** — ⚠️ Five tags of lifecycle-only swaps (`fitz.open` → `open_pdf`) in `extract_equipment`, `extract_magic_items`, `extract_features`, `extract_spells`, `extract_monsters`. **No behavioral change; engine binding not advanced.** Durable artifact: five parity tests pinning each extractor's byte output against the shipped SRD PDF. The five tags are retained for honesty.
- **v0.37.1** — (a) Three real engine bindings landed: `extract_features` and `extract_magic_items` onto a new `font_fingerprint_walk` pattern (span-mode and line-mode), `extract_spells` onto a new `font_stateful_walk` pattern. Total bespoke logic replaced: ~450 lines across the three extractors. `extract_monsters` declined at the 2-caller threshold (bbox+column-aware spans, cross-page pre-accumulation, lookahead validation). Bound: 3/13. (b) `extract/patterns.py` (1648 lines) split into `extract/patterns/` package, one module per pattern engine plus `_shared.py`/`_types.py`/`_dispatch.py`; public surface unchanged. (c) Bbox/column primitives lifted from `extract_monsters` into `utils/pdf_layout.py` (`extract_columnar_spans`, `merge_spans_into_lines`, `determine_column`, `merge_bboxes`, `color_to_rgb`); monsters shrunk 631 → 442 lines. (d) Producer-side strict validator (`src/srd_builder/utils/validate.py`) overhauled: all 16 datasets validated against the bundled schemas, every error collected via `iter_errors` and categorized by `<validator>@<json-path>`, machine-readable JSON report via `--report PATH`, strict-by-default with `--report-only` for iteration. Surfaced (and pinned) the 491-item schema-validation gap reported in the Blackmoor v0.37.0 integration review. (e) FIX(classes): `spellcasting.ability` now emits `charisma`/`wisdom`/`intelligence` (full names matching `class.schema.json` enum) instead of `Cha`/`Wis`/`Int`; closes 8/491. Full design pass + outcomes recorded in [docs/BACKLOG.md](docs/BACKLOG.md).
- **v1.0.0** — Frozen schema + stable consumer API 🚀

## License

Code is MIT licensed (see [LICENSE](LICENSE)). Generated datasets inherit the license of the
source documents (e.g. CC-BY 4.0 for Wizards of the Coast SRDs); document attribution in any
outputs you share.
