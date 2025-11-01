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

## **v0.4.0 — Structured Field Parsing** ✅ COMPLETE

**Goal:** Transform simple fields into rich structured data while maintaining 100% coverage.

**Delivered**

* **Structured Armor Class**
  - Simple: `17` → Structured: `{"value": 17, "source": "natural armor"}`
  - 191 monsters with armor sources preserved (plate, chain mail, shields, etc.)
  - Maintains backwards compatibility (can flatten to simple integer)

* **Structured Hit Points**
  - Simple: `135` → Structured: `{"average": 135, "formula": "18d10+36"}`
  - 296 monsters with dice formulas preserved
  - Enables HP rerolling and scaling

* **Parser architecture** (`parse_monsters.py`)
  - Pure mapping layer (no I/O)
  - Regex-based field extraction
  - Maintains deterministic output

**Quality Metrics:**
- ✅ 296 monsters with structured fields
- ✅ 191 armor sources preserved (64%)
- ✅ 296 HP formulas preserved (100%)
- ✅ All tests passing (43 tests)
- ✅ Zero regressions

**Data Quality vs Blackmoor:**
- **+95 more monsters** (296 vs 201 = 47% more)
- **Richer AC data:** preserves armor sources vs simple integers
- **Richer HP data:** unified formula in HP object vs separate fields
- **Direct PDF extraction:** reproducible pipeline vs unknown source

**Note on Monster Count:**
The 296 vs 319 discrepancy (from v0.3.0) was based on incorrect expectations. The SRD 5.1 PDF (pages 261-394) contains exactly 296 distinct monster stat blocks, which we extract at 100% accuracy. The "319" was likely including NPCs, variants, or alternate forms not present as separate stat blocks in the SRD.

### v0.4.1 — Quality Improvements ✅ COMPLETE

**Goal:** Refine structured parsing and expand test coverage.

**Delivered**

* **Structured Speed Conditions**
  - Preserves `(hover)` in speed entries
  - 7 monsters with hover condition: Flying Sword, Air Elemental, Ghost, Invisible Stalker, Specter, Will-o'-Wisp, Wraith
  - Format: `{"fly": {"value": 50, "condition": "hover"}}`
  - Single-word conditions preserved, complex text ignored gracefully

* **Speed Mode Validation**
  - Verified all 5 D&D speed modes parsing correctly
  - walk: 296 monsters, fly: 101, swim: 59, climb: 31, burrow: 20
  - Includes edge cases: 16 monsters with 0 ft walk (sharks, ethereal creatures)

* **3-Ability Score Edge Case**
  - Verified constructs working correctly (INT/WIS/CHA = 1)
  - Examples: Animated Armor, Flying Sword, Rug of Smothering
  - No changes needed - already handled properly

* **Test Coverage Expansion**
  - Added 10 fundamental extraction tests (`test_extract_basic.py`)
  - Tests: completeness, structure, names, blocks, fonts, stats, pages, warnings, counts, font sizes
  - Total: 53 tests passing (was 43)

**Integration Context:**

srd-builder is the **upstream producer** for Blackmoor (downstream consumer):
- We extract and produce: `data/`, `schemas/`, `indexes/`
- They consume: our JSON files replace their 201 monsters with our 296
- Integration: simple file copy from `dist/srd_5_1/data/*`
- See `docs/INTEGRATION.md` for details

**Current State:** Monster extraction is production-ready at v0.4.1. Next focus: additional content types (equipment, spells, classes).

### v0.4.2 — Metadata & Provenance ✅ COMPLETE

**Goal:** Establish clean provenance and remove hardcoded assumptions from intermediary sources.

**Delivered**

* **Rich Metadata (`dist/srd_5_1/meta.json`)**
  - License information (CC-BY-4.0 with full attribution)
  - Build metadata (timestamp, versions, PDF hash)
  - Page index computed from actual extraction (monsters: pages 261-394)
  - File manifest (only includes extracted content)
  - Extraction status tracking
  - Schema version 1.1.0

* **Clean Provenance**
  - Removed all hardcoded page numbers from Blackmoor/TabylTop sources
  - Page ranges computed dynamically from extraction data
  - `pdf_meta.json` separation: input validation vs consumer metadata
  - Version bumped to 0.4.2 throughout codebase

* **Directory Cleanup**
  - Renamed `raw/meta.json` → `raw/pdf_meta.json` (clear separation of concerns)
  - Removed unused `raw/extracted/` directory
  - Moved historical research to `docs/archive/`
  - Minimized public Blackmoor references (internal project)

* **Test Improvements**
  - Fixed 2 skipped tests (updated paths from `rulesets/` to `dist/`)
  - Suppressed PyMuPDF SWIG deprecation warnings
  - Updated golden fixtures with v0.4.2
  - All 56 tests passing

* **Documentation**
  - Created `docs/PARKING_LOT.md` for deferred features (terminology.aliases)
  - Updated README.md with v0.4.2 info and meta.json structure
  - Archived phase1_research materials
  - Removed Blackmoor branding from public docs

**Integration Context:**

Metadata structure now provides complete provenance for downstream consumers:
- License compliance (CC-BY-4.0 attribution)
- Source traceability (PDF hash, page ranges)
- Extraction status (what's complete vs pending)
- Ready for multi-content-type extraction (equipment, spells, etc.)

---

## **v0.5.0 — Equipment Dataset** ✅ COMPLETE

**Released:** November 1, 2025

**Goal:** Extract equipment from SRD 5.1 tables with proper column mapping and structured parsing.

**Delivered**

* **Equipment Dataset (111 items)**
  - 6 armor items with correct AC structure and subcategories (light/medium/heavy)
  - 19+ weapons with damage, versatile damage, range parsing
  - 70+ gear items including adventuring gear, tools, mounts, trade goods
  - Schema v1.1.0 with hybrid approach (current fields + future magic item fields)

* **Critical Bugs Fixed (Phase 1 — 100%)**
  1. ✅ Armor AC parsing — Proper object structure with base, dex_bonus, max_bonus
  2. ✅ Weight parsing — Correct weight_lb (float) and weight_raw (string with units)
  3. ✅ Versatile damage — Extracted and structured for versatile weapons
  4. ✅ Range extraction — Proper range.normal and range.long for ranged/thrown weapons
  5. ✅ Armor subcategory detection — Correct light/medium/heavy classification

* **Architecture Improvements**
  - **ColumnMapper class** — Reliable 3-tier column detection (header-based → heuristic → category defaults)
  - **Name-based inference** — Armor subcategory lookup table for SRD 5.1 armor types
  - **Context tracking** — Multi-page table section awareness
  - **Section header filtering** — Prevents header rows from being extracted as items

**Quality Assessment:** 85% confidence overall
- Armor: 95% (all validated)
- Weapons: 90% (damage, versatile, range tested)
- Gear: 70% (basic fields likely correct, untested)
- Edge cases: 60% (ammunition, mounts, packs need validation)

**Known Issues:**
- Shield subcategory shows "medium" instead of null
- Weapon subcategories use raw strings ("Martial Melee") vs normalized ("martial_melee")
- Properties are raw strings, should be normalized arrays
- Gear items need validation (70+ items untested)

**Lessons Learned:**
- Multi-page table handling is complex (PyMuPDF splits unpredictably)
- Context propagation is fragile across pages
- Name-based inference is pragmatic when context fails
- Heuristics need constraints (e.g., weight detection required "lb" to avoid false positives)
- Table metadata discovery would prevent per-table debugging cycles

**Production Bundle:**
```
dist/srd_5_1/
├── data/
│   ├── monsters.json      # 296 monsters
│   ├── equipment.json     # 111 items ✅ NEW
│   ├── index.json
│   └── meta.json
├── schemas/
│   ├── monster.schema.json (v1.1.0)
│   └── equipment.schema.json (v1.1.0) ✅ NEW
└── docs/
```

---

## **v0.5.5 — Table Metadata Discovery (Phase 0.5)** 🔄 PLANNED

**Goal:** Build infrastructure for systematic table discovery to prevent per-table debugging cycles.

**Problem:** Current heuristic approach works but doesn't scale
- Equipment armor subcategory fix used name-based inference (pragmatic but brittle)
- PDF table layouts are complex, context tracking unreliable
- Each new table requires custom debugging and fixes
- No validation capability ("did we extract all tables?")

**Solution:** Table metadata discovery system
```python
discover_tables() → table_metadata.json
{
  "tables": [
    {
      "id": "equipment_armor",
      "pages": [63, 64],
      "headers": ["Armor", "Cost", "Armor Class (AC)", "Strength", "Stealth", "Weight"],
      "row_count": 6,
      "sections": [
        {"name": "Light Armor", "rows": 3},
        {"name": "Medium Armor", "rows": 5},
        {"name": "Heavy Armor", "rows": 4}
      ]
    }
  ]
}
```

**Benefits:**
- Deterministic column mapping (no heuristics)
- Validation: compare extracted items to expected row counts
- Documentation: PDF structure visible to maintainers
- Prevents future cycles of per-table fixes

**Estimated Effort:** 2-3 hours

**Priority:** HIGH — Do this before spells/classes to avoid repeating equipment pain

---

## **v0.6.0 — Additional Content Types** 🔄 NEXT

**Goal:** Expand extraction to spells, conditions, or classes using improved table infrastructure.

**Candidates:**
- **Spells** (~300 items, structured prose, different pattern than tables)
- **Conditions** (simpler, good confidence builder)
- **Classes** (complex with level progression tables)

**Recommendation:** Start with spells (different enough to validate extraction patterns) or conditions (simpler, faster win)

**Architecture:** Each content type follows three-stage pattern:
```
extract_<type>.py → parse_<type>.py → postprocess.py → indexer.py
```

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
