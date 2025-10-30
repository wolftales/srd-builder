# 🧭 SRD-Builder — Roadmap (PDF ➜ JSON)

As of **v0.1.0**, the builder guarantees a stable directory layout,
writes a deterministic `build_report.json`, and records an optional
`pdf_sha256` when a source PDF is present. Data extraction begins in v0.2.0,
but the long-term vision remains: ingest **source PDFs** under
`rulesets/<ruleset>/raw/*.pdf` and produce **deterministic JSON datasets** in
multiple stages.

> Next milestone: **v0.3.0 focuses entirely on PDF extraction** so the
> fixtures used today can be replaced with real source pulls.

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

### **v0.1.1 — Enhanced Build & Validation** ✅

**Improvements:**

* Build now ensures proper directory layout (`raw/`, `raw/extracted/`, `dist/data/`)
* PDF hash tracking - computes SHA256 and stores in `rulesets/<ruleset>/raw/meta.json`
* Validation confirms `build_report.json` exists before checking datasets
* PDF integrity verification - validates hash when PDF present
* Added smoke test for basic build functionality
* Better error messages and graceful handling of missing files

*All changes backwards compatible with v0.1.0.*

---

## **v0.2.0 — End-to-End Pipeline** ✅

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

> **Intent:** Confirm the complete data pipeline functions deterministically using controlled fixture data.

**Clarify schema stage:**

> `validate.py` confirms `monsters.json` complies with `/schemas/monster.schema.json` and that no timestamps exist in outputs.

**End with a definition of done checklist:**

```
✅ build and validate commands run cleanly
✅ deterministic outputs under dist/
✅ schema validation passes
✅ CI green (ruff, black, pytest)
```

*Status:* **COMPLETE** - All objectives achieved. Pipeline produces deterministic, validated output with metadata wrapper and expanded test coverage.

---

## **v0.3.0 — PDF Extraction** 🔄 IN PROGRESS

**Goal:** extract *monsters* text blocks directly from the PDF
and serialize them as **raw, unprocessed JSON**.

**Status:** ~75% complete

### Completed ✅

* **Extraction module** (`src/srd_builder/extract_monsters.py`)
  - 296 monsters extracted from pages 261-394
  - Font metadata (name, size, color, flags)
  - Layout info (column, bbox, positioning)
  - Page numbers per monster
  - Verbatim text blocks with formatting preserved
  - Zero extraction warnings

* **Validation framework** (`src/srd_builder/validate_monsters.py`)
  - Category completeness checks (8 categories, 44 known monsters)
  - Count validation (290-320 range)
  - Uniqueness verification
  - Alphabetic distribution analysis
  - All tests passing

* **Build integration** (`build.py`)
  - Extraction runs automatically during build
  - Outputs to `rulesets/<ruleset>/raw/monsters_raw.json`
  - PDF SHA-256 tracking in metadata
  - Backward compatible with legacy format

**Outputs**

```
rulesets/<ruleset>/raw/monsters_raw.json    # 296 monsters with rich metadata
```

**Contents of `monsters_raw.json`:**

* One entry per monster with `name`, `pages`, `blocks`, `markers`, `warnings`
* Each block contains: `text`, `font`, `size`, `color`, `bbox`, `column`, `page`
* Fields unparsed — blocks array ready for parser consumption
* Page references and layout metadata retained

**Integration**

* ✅ `build.py` calls `extract_monsters(pdf_path)` when PDF present
* ✅ Computes and records PDF SHA-256 in extraction metadata
* ✅ `_load_raw_monsters()` supports new format (tries `monsters_raw.json` first)

### In Progress 🔄

* **Parser update** (`parse_monsters.py`)
  - Need to read `blocks` array and extract stat block fields
  - Size, type, alignment, AC, HP, abilities, speeds, etc.
  - Legacy parser only normalized pre-parsed fields
  - New work: actual parsing from semi-structured text blocks

### Remaining 📋

* **Extraction tests**
  - Test single monster extraction
  - Category detection
  - Column handling
  - Cross-page monsters

* **Cross-page validation**
  - Verify monsters spanning multiple pages work correctly
  - Test column wrap detection (Gemini YELLOW flag)

### Quality Metrics vs TabylTop

**Coverage:**
- ✅ 296 monsters (vs TT's 319 which included NPCs/appendices/conditions)
- ✅ All 8 core categories complete
- ✅ Zero duplicates
- ✅ Full Monster Manual section (pages 261-394)

**Data Richness:**
- ✅ Font metadata - **NEW** (TT didn't have)
- ✅ Layout info - **NEW** (TT didn't have)
- ✅ Page numbers - **same as TT**
- ✅ Verbatim text - **better** (TT normalized too early)
- ✅ Multiple blocks - **NEW** (TT flattened structure)

**Goal:** ✅ "Extracting directly from PDF at least as well as TabylTop"

### Validation Backlog (Post-v0.3.0)

Tasks to rigorously defend the 296 vs 319 count:

* Document the 23-entry delta with evidence
  - List specific non-monster entries from reference JSON
  - Examples: "Appendix MM-B", "Blinded" condition, "Actions" headers
* Manual spot-check sample
  - Verify random monsters from reference are in our 296
  - Check edge cases (first/last monsters, multi-page entries)
* Create comparison report
  - Side-by-side: what's in 319 but not 296, and why
  - Categorize: NPCs (page 60), appendices (post-394), conditions, chapter headers
* Be transparent in documentation
  - "We believe 296 is correct based on [evidence]"
  - Provide reproducible validation steps

*These validation tasks ensure defensibility for public project.*

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
