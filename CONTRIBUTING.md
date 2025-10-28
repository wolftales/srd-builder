# Contributing to srd-builder

Thanks for taking a look! This project keeps things intentionally small and predictable so we
can iterate on the extraction pipeline safely. A few friendly guardrails:

## Basics

- **Never commit SRD PDFs or raw text.** Keep source documents in `rulesets/*/raw/` locally —
  that path is ignored by git and blocked by CI/pre-commit.
- **Stay boring.** Small, focused pull requests are easiest to review.
- **Deterministic outputs.** Avoid timestamps or random ordering in generated datasets.

## Local setup

```bash
git clone https://github.com/wolftales/srd-builder.git
cd srd-builder
pip install -e ".[dev]"
pre-commit install
```

Run the full check suite before pushing:

```bash
pre-commit run --all-files
pytest
```

## Style & tests

- Ruff, Black, and isort keep formatting in check via pre-commit.
- Add or update tests for any new parsing/validation behavior.
- Missing sample data is fine — tests and validators should skip gracefully when files are absent.

## Licensing

Code is MIT. Data generated from SRD sources inherits the source license (for example, CC-BY
4.0). Please keep attribution metadata intact when you ship outputs.
