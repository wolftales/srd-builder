# Contributing to srd-builder

Thanks for checking out **srd-builder**.
It’s mainly a personal tool for building structured SRD data, but contributions and small improvements are welcome.

---

## Basics

* **Don’t commit source PDFs or SRD text.**
  If you’re working with SRD material locally, keep it outside the repo or in a private folder that isn’t committed.
  (You can add `rulesets/srd_xx/raw/` to your `.gitignore` if you want a local place for those files.)

* **Code style**
  Run this before committing to fix formatting and lint errors:

  ```bash
  pre-commit run --all-files
  ```

  It handles things like Ruff, Black, and JSON checks.

* **Testing**
  Every new feature or parser should have a test in `tests/`.
  Run:

  ```bash
  pytest
  ```

  All tests should pass before pushing.

* **Repeatable outputs**
  The same input should always create the same output files — no timestamps or random ordering.

* **Licenses**
  Code is under MIT.
  Data you generate follows the license of its source (CC-BY, OGL, ORC, etc.).
  Include proper attribution in any exported metadata.

* **Keep changes small**
  Focused pull requests are easier to review and merge.
  Use simple branch names like `feat/parser-update` or `fix/validation`.

---

## Local Setup

```bash
git clone https://github.com/wolftales/srd-builder.git
cd srd-builder
pip install -e ".[dev]"
pre-commit install
pytest
```

---

## Questions

If something doesn’t work or you’re unsure how to approach it, open an issue.
A short, clear description (and an example if you can) is all that’s needed.

---
