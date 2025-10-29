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
pre-commit run --all-files
pytest
```

### Build scaffold

The current build entry point only prepares output directories and metadata, leaving room for
future extraction logic.

```bash
python -m srd_builder.build --ruleset srd_5_1 --format json --out dist
```

This produces `dist/srd_5_1/build_report.json` with version metadata and a timestamp. Actual
content generation remains deterministic: leave timestamps out of dataset files.

### Validation helpers

Validation routines use JSON Schema and skip gracefully if sample data is missing.

```bash
python -m srd_builder.validate --ruleset srd_5_1
```

If `rulesets/srd_5_1/data/monsters.json` is present the validator checks it against
`schemas/monster.schema.json`. Otherwise it simply reports the missing dataset.

## Repository layout

```shell
srd-builder/                # Build + validation entry points
├── src/srd_builder/
│   ├── __init__.py
│   ├── build.py             # CLI orchestrator: --ruleset, --format, --out
│   ├── validate.py          # JSON Schema + sanity checks
│   ├── postprocess.py       # (from polish_data.py; pure functions)
│   ├── indexer.py           # builds index maps (ByName/CR/Type/Size)
│   ├── pdf_segment.py       # (next PR) PyMuPDF blocks/lines
│   ├── parse_equipment.py   # (next PR)
│   └── parse_monsters.py    # (later)
├── rulesets/
│   └── srd_5_1/
│       ├── manifest.json    # edition config (anchors, license, etc.)
│       ├── data/            # output JSON
│       └── raw/             # (ignored) local PDFs only
├── schemas/                 # JSON Schema definitions
│   ├── monster.schema.json
│   ├── equipment.schema.json
│   └── meta.template.json
├── tests/                    # code and schema tests
│   ├── test_json_sanity.py
│   └── test_schema_monster.py
├── .github/workflows/ci.yml
├── pyproject.toml
├── CONTRIBUTING.md
├── README.md
└── .gitignore
```

## License

Code is MIT licensed (see [LICENSE](LICENSE)). Generated datasets inherit the license of the
source documents (e.g. CC-BY 4.0 for Wizards of the Coast SRDs); document attribution in any
outputs you share.
