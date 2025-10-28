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

```
src/srd_builder/    # Build + validation entry points
schemas/            # JSON Schema definitions (monsters live, others stubbed)
tests/              # Minimal sanity and schema tests
rulesets/*/raw/     # Ignored: place local source PDFs here when developing
```

## License

Code is MIT licensed (see [LICENSE](LICENSE)). Generated datasets inherit the license of the
source documents (e.g. CC-BY 4.0 for Wizards of the Coast SRDs); document attribution in any
outputs you share.
