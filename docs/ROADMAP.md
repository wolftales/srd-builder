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

## **v0.3.0 — PDF Extraction & Parsing** ✅ COMPLETE

**Goal:** Extract monsters from PDF and parse all stat block fields into structured JSON.

**Status:** **COMPLETE** (v0.3.4 released)

### Delivered ✅

* **Extraction module** (`src/srd_builder/extract_monsters.py`)
  - 296 monsters extracted from pages 261-394
  - Font metadata (name, size, color, flags)
  - Layout info (column, bbox, positioning)
  - Page numbers per monster
  - Verbatim text blocks with formatting preserved
  - Zero extraction warnings

* **Parser implementation** (`parse_monsters.py`)
  - **18 fields at 100% coverage** when present in PDF
  - Font-based pattern recognition (12pt Bold names, 9.84pt stats)
  - Multi-block handling (split labels, cross-block values)
  - Edge case handling (split size/type, multi-line traits)
  - 296/296 monsters fully parsed (100% schema compliance)

* **Fields parsed:**
  - Core: name, size, type, alignment, AC, HP, speed
  - Abilities: strength, dexterity, constitution, intelligence, wisdom, charisma
  - Combat: saving throws, skills, damage resistances/immunities/vulnerabilities, condition immunities
  - Traits: traits, actions, reactions, legendary actions
  - Meta: senses, languages, challenge rating, XP value, page numbers
  - Summary: first trait text as mechanical summary

* **Validation framework** (`src/srd_builder/validate_monsters.py`)
  - Category completeness checks (8 categories, 44 known monsters)
  - Count validation (296 extracted, ~319 expected = 92.8% coverage)
  - Uniqueness verification
  - Field-by-field coverage analysis
  - Schema compliance validation

* **Build integration** (`build.py`)
  - Extraction runs automatically during build
  - PDF SHA-256 tracking in metadata
  - Schema version 1.1.0 with new fields

**Outputs**

```
rulesets/<ruleset>/raw/monsters.json        # 296 parsed monsters
dist/<ruleset>/data/monsters.json           # normalized output
dist/<ruleset>/data/index.json              # lookup maps
```

### Quality Metrics

**Coverage:**
- ✅ 296 monsters parsed (92.8% of expected 319)
- ✅ 18 fields at 100% coverage when present
- ✅ 101% trait detection (better than raw label count)
- ✅ Zero critical issues
- ✅ All 8 core categories complete

**vs Blackmoor Parser:**
- ✅ **+47% more monsters** (296 vs 201)
- ✅ **+4 additional fields** (languages, reactions, vulnerabilities, page refs)
- ✅ **Better accuracy:** 99% actions vs 93%, 100% senses vs 98%
- ✅ **Cleaner data:** no double-dash bugs or duplicate names

**Data Quality:**
- ✅ 100% schema compliance
- ✅ Deterministic output (no timestamps)
- ✅ 15 golden fixture tests passing
- ✅ Comprehensive quality reports (docs/COVERAGE_ANALYSIS.md)

### v0.3.x Releases

**v0.3.0** - Initial extraction + basic parsing
**v0.3.1** - Defense parsing (resistances/immunities/vulnerabilities/conditions)
**v0.3.2** - Skills and saving throws
**v0.3.3** - Senses, languages, 100% field coverage
**v0.3.4** - Split size/type fix, reactions parsing, feature-complete
**v0.3.5** - Summary and XP value fields, schema 1.1.0

---

## **v0.4.0 — Quality & Completeness** 🔄 NEXT

**Goal:** Address remaining edge cases and investigate missing monsters.

**Planned Enhancements**

* **Missing monsters investigation** (296 → 319)
  - Identify which 23 creatures we're missing
  - Manual PDF review for NPCs, variants, different formatting
  - Compare against official SRD creature index
  - Expand extraction patterns if needed

* **3-ability score edge case** (~62 monsters)
  - Handle constructs with only STR/DEX/CON (no INT/WIS/CHA)
  - Examples: Animated Armor, Flying Sword, Rug of Smothering
  - Currently these have valid scores, need verification

* **Structured field parsing** (leverage schema's object support)
  - Armor Class: `{"value": 17, "source": "natural armor"}`
  - Hit Points: `{"average": 135, "formula": "18d10+36"}`
  - Speed: More granular breakdown with conditions
  - Damage immunities/resistances/vulnerabilities: structured lists

* **Enhanced dice/bonus parsing**
  - Attack bonuses: separate to-hit from damage
  - Saving throw DC extraction
  - Condition duration parsing

* **Quality improvements**
  - Trait detection analysis (101% vs Blackmoor's 98%)
  - Validation against known monster patterns
  - Extended comparison with other parsers

**Current State:** Parser is feature-complete at 100% coverage for present fields. v0.4.0 focuses on completeness (finding missing monsters) and advanced structuring.

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
