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
# clone
git clone https://github.com/wolftales/srd-builder.git
cd srd-builder

# install developer tooling
pip install -e ".[dev]"
pre-commit install

# run checks
make pre-commit
make test
```

### Build pipeline (v0.14.0)

The build pipeline extracts monster, equipment, spell, table, lineage, and class data from PDF, parses stat blocks, normalizes fields, and builds indexes. **296 monsters**, **111 equipment items**, **319 spells**, **37 tables** (12 class progression + 25 equipment/reference), **13 lineages** (9 base + 4 subraces), and **12 classes** with full provenance tracking. v0.9.7 migrates travel_pace and size_categories tables from hardcoded to PDF extraction, removes non-SRD tables (cantrip_damage, spell_slots_by_level).

**Development workflow (fast iteration, data only):**
```bash
# Build JSON data files only - NO schemas or docs copied
# Output: 13 JSON files in dist/srd_5_1/
make output

# Verify data integrity
./scripts/verify_build.sh srd_5_1 dist dev
```

**Production workflow (complete bundle for distribution):**
```bash
# Build complete bundle: data + schemas + docs
# Output: 24 files (13 JSON + 8 schemas + 2 docs + README)
make bundle

# Verify complete bundle structure
./scripts/verify_build.sh srd_5_1 dist bundle
```

**Key difference:**
- `make output` → Fast (data only), use for development/testing
- `make bundle` → Complete (adds schemas/, docs/, README.md), use for releases/packaging

**Validation:**
```bash
python -m srd_builder.validate --ruleset srd_5_1
```

**Development output:**
```
dist/srd_5_1/
├── monsters.json          # 296 creature stat blocks
├── equipment.json         # 106 items
├── spells.json            # 319 spells
├── tables.json            # 37 reference tables (12 class progression + 25 equipment/reference)
├── lineages.json          # 13 character lineages (9 base + 4 subraces)
├── classes.json           # 12 character classes
├── index.json             # Lookup indexes (all datasets)
├── meta.json              # Dataset metadata (license, provenance)
└── build_report.json      # Build metadata (version, timestamp)
```

**Production bundle output:**
```
dist/srd_5_1/
├── monsters.json          # 296 creature stat blocks
├── equipment.json         # 106 items
├── spells.json            # 319 spells
├── tables.json            # 37 reference tables
├── lineages.json          # 13 character lineages
├── classes.json           # 12 character classes
├── index.json             # Lookup indexes (all datasets)
├── meta.json              # Dataset metadata (license, provenance)
├── README.md              # Consumer documentation
├── build_report.json      # Build metadata (version, timestamp)
├── schemas/
│   ├── monster.schema.json
│   ├── equipment.schema.json
│   ├── spell.schema.json
│   ├── table.schema.json
│   ├── lineage.schema.json
│   └── class.schema.json
└── docs/
    ├── SCHEMAS.md
    └── DATA_DICTIONARY.md
```

**Pipeline stages:**

1. **Extract** (`extract_monsters.py`) - PDF text extraction with font metadata
2. **Parse** (`parse_monsters.py`) - Stat block parsing (18 fields)
3. **Postprocess** (`postprocess/`) - Normalize and clean entries
4. **Index** (`indexer.py`) - Build lookup tables
5. **Validate** (`validate.py`) - JSON Schema validation

**Parsed fields (27):** id, simple_name, name, summary, size, type, alignment, armor_class, hit_points, hit_dice, speed, ability_scores, saving_throws, skills, damage_resistances, damage_immunities, damage_vulnerabilities, condition_immunities, senses, languages, challenge_rating, xp_value, traits, actions, reactions, legendary_actions, page.

### Consume the dataset (Python)

```python
import json, pathlib
p = pathlib.Path("dist/srd_5_1/monsters.json")
data = json.loads(p.read_text(encoding="utf-8"))
print(f"Schema: {data['_meta']['schema_version']}, Monsters: {len(data['items'])}")

# Example: Find CR 10 monsters
cr10 = [m for m in data["items"] if m["challenge_rating"] == "10"]
for monster in cr10:
    print(f"{monster['name']}: {monster['xp_value']} XP - {monster['summary']}")
```

### Determinism

Same inputs → same bytes. Arrays are sorted where order isn’t meaningful; dataset files contain no timestamps (only `build_report.json` records time).

### Identifier policy

Every monster and nested entry exposes both an `id` and `simple_name`. Identifiers are lowercase ASCII snake_case and match the regular expression `[a-z0-9_]+`. Top-level IDs are prefixed with `monster:`.

### Development workflow

```bash
# Local checks before committing
make pre-commit    # Run all pre-commit hooks
make lint          # Ruff + Black formatting checks
make test          # Run pytest
make ci            # Full CI simulation (lint + test)

# Version bump (automates __init__.py, fixtures, README, tests, commit)
python scripts/bump_version.py 0.6.5
python scripts/bump_version.py 0.7.0 --no-commit  # Preview changes without committing
```

### Validation

Validation uses JSON Schema to ensure output quality:

```bash
python -m srd_builder.validate --ruleset srd_5_1
```

The validator checks `dist/srd_5_1/data/monsters.json` against
`schemas/monster.schema.json` and reports any schema violations.

## Repository layout

```shell
srd-builder/
├── src/srd_builder/
│   ├── build.py             # CLI orchestrator: --ruleset, --out
│   ├── validate.py          # JSON Schema validation
│   ├── parse_monsters.py    # Field mapping from raw to structured
│   ├── postprocess/         # Normalization & cleanup functions
│   └── indexer.py           # Build lookup indexes
├── rulesets/
│   └── srd_5_1/
│       └── raw/             # (gitignored) Local PDFs and fixtures
├── dist/                     # Build output (gitignored)
│   └── srd_5_1/
│       ├── build_report.json
│       └── data/
│           ├── monsters.json
│           └── index.json
├── schemas/                  # JSON Schema definitions
│   └── monster.schema.json
├── tests/
│   ├── fixtures/            # Test data (raw & normalized)
│   └── test_*.py
├── docs/
│   └── ROADMAP.md           # Development roadmap
├── .github/workflows/
│   └── ci.yml               # GitHub Actions CI
├── Makefile                 # Development shortcuts
├── pyproject.toml
└── .pre-commit-config.yaml
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full development plan.

- ✅ **v0.1.0** - Foundation (CI, build infrastructure, validation)
- ✅ **v0.2.0** - End-to-end pipeline with fixture data
- ✅ **v0.3.0** - PDF extraction module (296 monsters)
- ✅ **v0.4.0** - Structured field parsing (AC, HP objects)
- ✅ **v0.5.0** - Equipment dataset complete (111 items)
- ✅ **v0.5.1** - Action parsing & ability modifiers (schema v1.2.0)
- ✅ **v0.6.2** - Spells dataset complete (319 spells, schema v1.3.0)
- ✅ **v0.6.3** - Fixed build_report.json path reference
- ✅ **v0.6.4** - Spell parsing improvements (ritual, area, healing, attack effects)
- ✅ **v0.6.5** - Version management tooling
- ✅ **v0.7.0** - Reference tables dataset (12 class progression tables)
- ✅ **v0.7.1** - Classes & Lineages (character creation + terminology aliases)
- ✅ **v0.9.0** - Equipment tables (armor, weapons, exchange rates)
- ✅ **v0.9.1** - Equipment tables (adventure gear, tools, container capacity)
- ✅ **v0.9.2** - Equipment tables complete (25 equipment/pricing tables)
- ✅ **v0.9.3** - Text parser refactor (utilities + migration guide)
- ✅ **v0.9.4** - Migrate CALCULATED tables (ability_scores to PDF extraction)
- ✅ **v0.9.5** - Pattern-based architecture (metadata-driven table extraction)
- ✅ **v0.9.6** - TOC & Page Index (PAGE_INDEX with 23 sections, accurate page numbers)
- ✅ **v0.9.7** - Migrate REFERENCE tables (travel_pace, size_categories from PDF; removed non-SRD tables)
- 🎯 **v0.9.8** - Migrate CLASS_PROGRESSIONS (12 class tables to PDF extraction)
- 🎯 **v0.10.0** - Conditions dataset (~15 conditions)
- 🎯 **v0.10.0** - Features dataset (class/racial features)
- 🎯 **v0.11.0** - Rules dataset (core mechanics, variant rules)
- 🎯 **v0.12.0** - Rules Dataset (core mechanics)
- ✅ **v0.14.0** - Deterministic metadata + prose datasets (conditions, diseases, madness, poisons)
- 🎯 **v0.15.0** - Quality & Polish (final cleanup before v1.0.0)
- 🎯 **v1.0.0** - Complete SRD 5.1 in JSON (9 datasets) 🚀

## Testing

```bash
# Run unit/integration tests (no build required)
make test
# OR: pytest -m "not package"

# Run ALL tests including package validation (requires built package)
make test-all
# OR: pytest

# Run only package validation tests
make test-package
# OR: pytest -m package

# Run specific test categories
pytest tests/test_parse_actions.py  # Action parsing tests
pytest tests/test_raw_extraction.py  # Raw PDF extraction validation
pytest tests/test_golden_monsters.py  # End-to-end pipeline test
```

**Test Categories:**
- **Unit tests** (no build required): Parsing, postprocessing, extraction logic
- **Package tests** (requires `make output`): Validates built output in `dist/`
  - Schema version consistency
  - Meta.json structure
  - Dataset structure validation

**Coverage:**
- `test_raw_extraction.py` - Validates raw PDF extraction output structure (monsters_raw.json)
- `test_parse_*.py` - Unit tests for parsing modules (monsters, equipment, actions)
- `test_golden_*.py` - End-to-end tests comparing pipeline output to fixtures
- `test_schema_versions.py` - Schema version consistency (unit + package tests)
- 92 tests passing

## Use Cases

The generated datasets are designed for:

- **VTT Integrations** - Roll20, Foundry VTT, Fantasy Grounds
- **Mobile Apps** - Character sheets, monster reference, DM tools
- **AI/LLM Applications** - D&D chatbots, rule assistants, content generation
- **Campaign Tools** - Encounter builders, initiative trackers
- **Analysis & Research** - Game balance studies, statistical modeling

### Validation Examples

```bash
# Validate with jsonschema (Python)
jsonschema -i dist/srd_5_1/monsters.json schemas/monster.schema.json

# Or in code
import json
from jsonschema import Draft202012Validator

with open('schemas/monster.schema.json') as f:
    schema = json.load(f)
with open('dist/srd_5_1/data/monsters.json') as f:
    data = json.load(f)

validator = Draft202012Validator(schema)
for error in validator.iter_errors(data['items'][0]):
    print(error.message)
```

## Versioning

srd-builder uses **three version numbers**:

- **Package version** (`__version__` = `0.5.2`) - The data/package we produce
- **Extractor version** (`EXTRACTOR_VERSION` = `0.3.0`) - Raw extraction format for all `*_raw.json` files
- **Schema version** (`1.2.0`) - JSON Schema validation rules (consumer data contract)

The **package version** tracks each release. The **extractor version** tracks how we extract from PDF (stable since v0.3.0). The **schema version** tracks the final data structure for consumers.

See [ARCHITECTURE.md](docs/ARCHITECTURE.md#version-management) for detailed version management documentation.

## License

Code is MIT licensed (see [LICENSE](LICENSE)). Generated datasets inherit the license of the
source documents (e.g. CC-BY 4.0 for Wizards of the Coast SRDs); document attribution in any
outputs you share.
