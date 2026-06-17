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
# Clone repository
git clone https://github.com/wolftales/srd-builder.git
cd srd-builder

# Create and activate virtual environment (Python 3.14+)
python3.14 -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# Install project (editable mode, Python 3.14 compatible)
pip install -e . --config-settings editable_mode=compat

# Add SRD PDF to enable full extraction (gitignored)
# Place your CC-BY licensed SRD_CC_v5.1.pdf in: rulesets/srd_5_1/

# Build complete bundle (data + schemas + docs)
make bundle

# Output is ready in dist/srd_5_1/
ls -lh dist/srd_5_1/
cat dist/srd_5_1/build_report.json
```

Done! You now have a complete SRD 5.1 bundle ready to share. Load and use it:

```python
import json
from pathlib import Path

# Load any dataset
data = json.loads(Path("dist/srd_5_1/monsters.json").read_text())
print(f"Loaded {len(data['items'])} monsters")
```

> **Note:** Without the SRD PDF in `rulesets/srd_5_1/`, PDF-extracted datasets
> (monsters, spells, equipment, magic_items) will be empty. Static datasets
> (classes, lineages, conditions, etc.) still build correctly. The `raw/`
> subdirectory is for build-generated `*_raw.json` intermediates, not the PDF.

See "Building datasets" below for all available build options.

### Build pipeline (v0.23.0)

The build pipeline extracts data from the SRD PDF, parses and normalizes it, validates against
JSON Schema, and emits 16 dataset files plus a search index. Latest build: **1,696 items across 16 datasets**.
See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full pipeline.

| Dataset | Count | Schema |
|---|---:|---|
| Monsters | 317 | v2.0.0 |
| Spells | 319 | v2.0.0 |
| Equipment | 259 | v2.0.0 |
| Magic Items | 240 | v2.0.0 |
| Features | 246 | v2.0.0 |
| Rules | 172 | v2.0.0 |
| Tables | 38 | v2.0.0 |
| Skills | 18 | v1.0.0 |
| Conditions | 15 | v2.0.0 |
| Poisons | 14 | v2.0.0 |
| Damage Types | 13 | v1.0.0 |
| Lineages | 13 | v2.0.0 |
| Classes | 12 | v2.0.0 |
| Weapon Properties | 11 | v1.0.0 |
| Ability Scores | 6 | v1.0.0 |
| Diseases | 3 | v2.0.0 |

Live counts are also written to `dist/srd_5_1/meta.json` under `inventory` on every build.

## Building datasets

Build SRD 5.1 JSON output for Blackmoor:

**With make (recommended):**
```bash
# Build complete bundle: data + schemas + docs + README
# Output: 16 dataset JSON files + 16 schemas + 2 docs + dynamically-generated README
make bundle
```

**Without make (direct command):**
```bash
PYTHONPATH=src python -m srd_builder.build --ruleset srd_5_1 --out dist --bundle
```

**Post-build validation:**
```bash
# Verify data integrity and schema compliance
PYTHONPATH=src python -m srd_builder.validate --ruleset srd_5_1

# Quick sanity check (item counts)
./scripts/smoke.sh srd_5_1 dist bundle
```

**Critical difference between build types:**

| | Data only | Complete bundle |
|---|---|---|
| **Data files** | ✅ 16 JSON files | ✅ 16 JSON files |
| **Schemas** | ❌ None | ✅ 16 schema files |
| **Documentation** | ❌ None | ✅ SCHEMAS.md, DATA_DICTIONARY.md |
| **README** | ❌ None | ✅ Consumer-facing README.md |
| **Speed** | ⚡ Fast | 🐢 Slightly slower |
| **Use case** | Development, testing, quick iteration | Releases, distribution, sharing |

**Output structure (with `make bundle`):**
```
dist/srd_5_1/
├── ability_scores.json    # 6 ability score definitions
├── classes.json           # 12 character classes
├── conditions.json        # 15 status conditions
├── damage_types.json      # 13 damage types
├── diseases.json          # 3 diseases
├── equipment.json         # 259 items (weapons, armor, gear)
├── features.json          # 246 class + lineage features
├── lineages.json          # 13 lineages (formerly races)
├── magic_items.json       # 240 magic items
├── monsters.json          # 317 creature stat blocks
├── poisons.json           # 14 poisons
├── rules.json             # 172 rules from 7 core chapters
├── skills.json            # 18 skills
├── spells.json            # 319 spells
├── tables.json            # 38 reference tables
├── weapon_properties.json # 11 weapon properties
├── index.json             # Lookup index (all datasets, with aliases)
├── meta.json              # Bundle metadata (versions, license, inventory)
├── build_report.json      # Build provenance (timestamp, builder version)
├── README.md              # Auto-generated consumer documentation
├── schemas/               # 16 JSON Schema files (one per dataset)
└── docs/                  # SCHEMAS.md, DATA_DICTIONARY.md
```

**Pipeline stages:**

1. **Extract** (`extract_monsters.py`) - PDF text extraction with font metadata
2. **Parse** (`parse_monsters.py`) - Stat block parsing (18 fields)
3. **Postprocess** (`postprocess/`) - Normalize and clean entries
4. **Index** (`indexer.py`) - Build lookup tables
5. **Validate** (`validate.py`) - JSON Schema validation

**Parsed fields (27):** id, simple_name, name, summary, size, type, alignment, armor_class, hit_points, hit_dice, speed, ability_scores, saving_throws, skills, damage_resistances, damage_immunities, damage_vulnerabilities, condition_immunities, senses, languages, challenge_rating, xp_value, traits, actions, reactions, legendary_actions, page.

A full inventory is written to `dist/srd_5_1/meta.json` under the `inventory` key after every build.

### Consume the dataset (Python)

After building, load and use the JSON data:

```python
import json
from pathlib import Path

# Load monsters dataset
monsters_file = Path("dist/srd_5_1/monsters.json")
monsters_data = json.loads(monsters_file.read_text(encoding="utf-8"))

print(f"Schema: {monsters_data['_meta']['schema_version']}")
print(f"Total monsters: {len(monsters_data['items'])}")

# Example: Find CR 10 monsters
cr10 = [m for m in monsters_data["items"] if m["challenge_rating"] == "10"]
for monster in cr10:
    print(f"{monster['name']}: {monster['xp_value']} XP - {monster['summary']}")

# Load spells
spells_file = Path("dist/srd_5_1/spells.json")
spells_data = json.loads(spells_file.read_text(encoding="utf-8"))
print(f"\nTotal spells: {len(spells_data['items'])}")

# Load classes with progression tables
classes_file = Path("dist/srd_5_1/classes.json")
classes_data = json.loads(classes_file.read_text(encoding="utf-8"))
for cls in classes_data["items"]:
    print(f"Class: {cls['name']} - {len(cls['hit_dice'])} hit dice")
```

### Determinism

Same inputs → same bytes. Arrays are sorted where order isn’t meaningful; dataset files contain no timestamps (only `build_report.json` records time).

### Identifier policy

Every monster and nested entry exposes both an `id` and `simple_name`. Identifiers are lowercase ASCII snake_case and match the regular expression `[a-z0-9_]+`. Top-level IDs are prefixed with `monster:`.

### Development workflow

**With make (recommended):**
```bash
# Local checks before committing
make pre-commit    # Run all pre-commit hooks
make lint          # Ruff formatting + linting checks
make test          # Run pytest
make ci            # Full CI simulation (lint + test)
```

**Without make (direct commands):**
```bash
# Format and lint
ruff format .
ruff check . --fix

# Run tests
pytest -q

# Type checking
mypy src

# Pre-commit hooks (all at once)
pre-commit run --all-files
```

### Verification

Validation uses JSON Schema to ensure output quality:

**With make:**
```bash
make smoke              # Dev build validation (item counts only)
make smoke MODE=bundle  # Bundle build validation (+ structure checks)
make release-check      # Determinism + item count validation
```

**Without make (direct commands):**
```bash
# Full schema validation
PYTHONPATH=src python -m srd_builder.validate --ruleset srd_5_1

# Quick sanity check (item counts)
./scripts/smoke.sh srd_5_1 dist

# Bundle structure validation
./scripts/smoke.sh srd_5_1 dist bundle

# Determinism verification (hash comparison + counts)
./scripts/release_check.sh srd_5_1 dist
```

See [docs/VERIFICATION_CHECKLIST.md](docs/VERIFICATION_CHECKLIST.md) for details on validation targets:
- `smoke`: Fast sanity check for development (item counts)
- `smoke MODE=bundle`: Bundle structure validation
- `release-check`: Full determinism verification (hash comparison + counts)

### Version Management

Version is automatically read from `pyproject.toml` at runtime via `importlib.metadata`:

```bash
# Bump version in pyproject.toml (handles docs/commits/tags automatically)
python scripts/bump_version.py 0.22.1

# Preview version changes without committing
python scripts/bump_version.py 0.23.0 --no-commit

# Verify current version
python -c "import srd_builder; print(srd_builder.__version__)"
```

## Repository layout

```shell
srd-builder/
├── src/srd_builder/
│   ├── build.py             # CLI orchestrator (--ruleset, --out, --bundle)
│   ├── validate.py          # JSON Schema validation
│   ├── extract/             # PDF extraction modules
│   ├── parse/               # Field parsing (one per dataset)
│   ├── postprocess/         # Normalization & cleanup
│   ├── assemble/            # Assembly + indexer
│   └── utils/               # Metadata, page index, helpers
├── rulesets/
│   └── srd_5_1/
│       ├── SRD_CC_v5.1.pdf  # (gitignored) Local source PDF
│       └── raw/             # (gitignored) Build-generated *_raw.json intermediates
├── dist/                    # Build output (gitignored)
│   └── srd_5_1/             # See "Output structure" above
├── schemas/                 # 17 JSON Schema definitions (source of truth)
├── tests/
│   ├── fixtures/            # Raw + normalized test data
│   └── test_*.py            # Pytest suite (292 tests)
├── docs/                    # ARCHITECTURE, ROADMAP, SCHEMAS, etc.
├── archive/                 # Historical snapshots + retired code/docs
├── scripts/                 # Build helpers, smoke checks, version bump
├── .github/workflows/ci.yml
├── Makefile
├── pyproject.toml
└── .pre-commit-config.yaml
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for the full history. **Latest release: v0.23.0** — audit, cleanup, and consumer-handoff readiness.

Key milestones:

- **v0.3.0–v0.7.x** — PDF extraction + structured field parsing
- **v0.9.x** — Equipment + reference tables + class progressions
- **v0.14.0** — Conditions, diseases, madness, poisons (deterministic prose pipeline)
- **v0.15.0** — Module reorganization + monster/spell refactor
- **v0.16.0** — Magic items dataset (240 items)
- **v0.17.0** — Rules dataset (172 rules, 7 chapters)
- **v0.18.0–v0.21.0** — Modular refactor, postprocess engine, cross-reference validation
- **v0.22.x** — Editable install + macOS `UF_HIDDEN` fixes; dynamic package version
- **v0.23.0** — Bundle README auto-generation, full schema coverage, inventory manifest, repo cleanup
- **v1.0.0** — Frozen schema + stable consumer API 🚀

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
- `test_raw_extraction.py` — Validates raw PDF extraction output structure (monsters_raw.json)
- `test_parse_*.py` — Unit tests for parsing modules (monsters, equipment, actions)
- `test_golden_*.py` — End-to-end tests comparing pipeline output to fixtures (one per dataset)
- `test_schema_versions.py` — Schema version consistency (unit + package tests)
- 292 tests passing

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
with open('dist/srd_5_1/monsters.json') as f:
    data = json.load(f)

validator = Draft202012Validator(schema)
for error in validator.iter_errors(data['items'][0]):
    print(error.message)
```

## Versioning

srd-builder uses **two version numbers**:

- **Package version** (read from `pyproject.toml` at runtime via `importlib.metadata`, currently `v0.23.0`) — the builder release.
- **Schema version** — each dataset schema in `schemas/*.schema.json` evolves independently (currently v1.0.0–v2.0.0). Schema versions are written into `dist/srd_5_1/meta.json` `schemas` on every build, and into each dataset's `_meta.schema_version`.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#version-management) for the detailed policy.

## License

Code is MIT licensed (see [LICENSE](LICENSE)). Generated datasets inherit the license of the
source documents (e.g. CC-BY 4.0 for Wizards of the Coast SRDs); document attribution in any
outputs you share.
