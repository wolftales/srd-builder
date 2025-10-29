# 🧭 SRD-Builder — Roadmap (PDF ➜ JSON)

The builder ingests **source PDFs** under `rulesets/<ruleset>/raw/*.pdf`
and produces **deterministic JSON datasets** in multiple stages.

```
PDF  ─►  text extraction  ─►  raw JSON (verbatim blocks)
        rulesets/<ruleset>/raw/extracted/monsters_raw.json
                       │
                       ▼
            parse_monsters.py (field mapping)
                       ▼
            postprocess.py (clean & normalize)
                       ▼
            dist/<ruleset>/data/monsters.json  ← clean, deterministic output
```
---

## **v0.1.0 — Foundation** ✅

**Goal:** get a working build command and CI flow.

**Delivers**

* `build.py` runs end-to-end and creates `dist/<ruleset>/build_report.json`.
* `validate.py` exists (even if stubbed).
* CI passes: ruff, black, pytest, mypy.
* Directory layout fixed:

  ```
  src/srd_builder/
  rulesets/<ruleset>/raw/
  dist/<ruleset>/
  ```

*Status:* **COMPLETE** - Infrastructure and tooling in place.

---

## **v0.2.0 — End-to-End Pipeline** 🚧

**Goal:** prove the full build pipeline works with **fixture data** (not PDF extraction yet).

**What Works**

```
rulesets/srd_5_1/raw/monsters.json  (fixture from tests/)
   │
   ├─► parse_monsters.py      → field mapping
   ├─► postprocess.py         → normalization & cleanup
   └─► indexer.py             → build lookups
   │
   ▼
dist/srd_5_1/data/monsters.json     # normalized output
dist/srd_5_1/data/index.json        # lookup maps
   │
   ▼
validate.py  ← schema validation passes
```

**Outputs**

```
dist/<ruleset>/build_report.json
dist/<ruleset>/data/monsters.json
dist/<ruleset>/data/index.json
```

**Commands**

```bash
python -m srd_builder.build --ruleset srd_5_1 --out dist
python -m srd_builder.validate --ruleset srd_5_1
```

*Purpose:* Validate that parse → postprocess → index → validate chain works correctly before tackling PDF extraction.

---

## **v0.3.0 — PDF Extraction**

**Goal:** extract *monsters* text blocks directly from the PDF
and serialize them as **raw, unprocessed JSON**.

**New Module**

```python
src/srd_builder/extract_monsters.py
```

**Outputs**

```
rulesets/<ruleset>/raw/extracted/monsters_raw.json
```

**Contents of `monsters_raw.json`:**

* One entry per monster block from the PDF.
* Fields mostly unparsed — strings for AC, HP, actions, etc.
* Page references and offsets retained.

**Integration**

* `build.py` calls `extract_monsters_from_pdf(pdf_path)` instead of loading pre-existing JSON
* Optional: compute and record PDF SHA-256 in `build_report.json`

*This is the "read from source PDF" milestone.*

---

## **v0.4.0 — Extraction Quality Pass (monsters)**

**Goal:** improve PDF segmentation fidelity.

**Planned**

* Better block detection (headers, "Armor Class", "Hit Points", "Actions", etc.).
* Robust dice/bonus parsing; multi-line traits/actions join rules.
* Handle edge cases (legendary actions, lair actions, regional effects).
* Page cross-check using page index metadata.

---

## **v0.5.0 — Additional Entities**

**Goal:** repeat the extraction+normalize flow for:

* Equipment
* Lineages
* (Later) Classes, Spells, Features

Each follows the same three-stage pattern:
`extract_*` → `parse_*` → `postprocess` → `indexer`.

---

## **v0.6.0 — Unified Build & Validation**

**Goal:** single `build_all()` to process all entities and a top-level `validate_all()` for all schemas and PDFs.

---

### Principles

* **Source of truth:** the PDF, not pre-existing JSON.
* **Fixtures:** used only for unit/golden tests.
* **Determinism:** identical inputs yield identical outputs.
* **Layered:** extract → parse → postprocess → index → validate.
* **No timestamps in dataset files.**

---
