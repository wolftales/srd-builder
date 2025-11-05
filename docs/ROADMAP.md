# 🧭 SRD-Builder — Roadmap (PDF ➜ JSON)

As of **v0.1.0**, the builder guarantees a stable directory layout,
writes a deterministic `build_report.json`, and records an optional
`pdf_sha256` when a source PDF is present. Data extraction begins in v0.2.0,
but the long-term vision remains: ingest **source PDFs** under
`rulesets/<ruleset>/raw/*.pdf` and produce **deterministic JSON datasets** in
multiple stages.

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

## 📊 Milestone Status

**Completed:**
- ✅ v0.1.0 — Foundation (infrastructure & tooling)
- ✅ v0.2.0 — End-to-End Pipeline (fixture-based validation)
- ✅ v0.3.0 — PDF Extraction (296 monsters from PDF)
- ✅ v0.4.0 — Structured Fields (AC, HP parsing)
- ✅ v0.5.0 — Equipment Dataset (111 items)
- ✅ v0.5.1 — Action Parsing & Ability Modifiers (structured combat)
- ✅ v0.6.2 — Spells Dataset (319 spells)
- ✅ v0.7.0 — Reference Tables (23 tables + indexer)
- ✅ v0.8.0 — Lineages Dataset (13 lineages)
- ✅ v0.8.1 — Alias System & PDF Metadata
- ✅ v0.8.2 — Classes Dataset (12 classes)
- ✅ v0.8.3 — Equipment Cleanup (proficiency field)
- ✅ v0.8.4 — Character Creation Blockers (ability modifiers, range structure)
- ✅ v0.8.5 — Spell Enhancements (healing 100%, AOE +43%)
- ✅ v0.8.6 — Spell Duration Restructure (concentration discoverability)
- ✅ v0.9.0 — Text-Based Table Extraction (coordinate breakthrough)
- ✅ v0.9.1 — Equipment Tables Expansion (adventure gear, tools, containers)
- ✅ v0.9.2 — Equipment Tables Complete (37 tables total)

**In Progress:**
- 🔄 v0.9.3 — Text Parser Refactor (Phase 2 of 3 complete, utilities + 5 parsers refactored)

**Planned:**
- 📋 v0.10.0 — Conditions Dataset (~15-20 conditions)
- 📖 v0.11.0 — Features Dataset (class/racial features)
- 📜 v0.12.0 — Rules Dataset (core mechanics)
- 🎨 v0.13.0 — Quality & Polish (final cleanup before v1.0.0)
- 🚀 v1.0.0 — Complete SRD 5.1 in JSON (stable release)

---

## 📦 Dataset Coverage (SRD 5.1 Complete Target)

This section tracks progress toward the complete SRD 5.1 dataset extraction.

| File | Status | Count | Version | Description |
|------|--------|-------|---------|-------------|
| `meta.json` | ✅ Complete | 1 | v0.1.0+ | Version, license, page index, terminology aliases |
| `monsters.json` | ✅ Complete | 296 | v0.4.2 | Monster statblocks (normalized) |
| `equipment.json` | ✅ Complete | 111 | v0.5.0 | Weapons, armor, adventuring gear |
| `spells.json` | ✅ Complete | 319 | v0.6.2 | Spell list with effects, components, casting |
| `tables.json` | ✅ Complete | 37 | v0.9.2 | Reference tables (12 class progression + 25 equipment/reference) |
| `lineages.json` | ✅ Complete | 13 | v0.8.0 | Races/lineages with traits |
| `classes.json` | ✅ Complete | 12 | v0.8.2 | Character classes with progression |
| `index.json` | ✅ Complete | - | v0.2.0+ | Fast lookup maps (by name, CR, type, etc.) |
| `conditions.json` | 📋 Planned | ~15-20 | v0.10.0 | Status conditions (poisoned, stunned, etc.) |
| `features.json` | 📋 Planned | TBD | v0.11.0 | Class/lineage features (Action Surge, Darkvision) |
| `rules.json` | 📋 Planned | TBD | v0.12.0 | Core mechanics, variant rules |

**Progress:** 8/11 datasets complete (73%)

**Completed Datasets:**
- ✅ Monsters (296 entries) - Monster statblocks with structured combat actions
- ✅ Equipment (111 items) - Weapons (37), Armor (14), Adventuring gear (60)
- ✅ Spells (319 spells) - Healing (100%), AOE (24.8%), Range (100%)
- ✅ Tables (37 tables) - 12 class progression + 25 equipment/reference tables
- ✅ Lineages (13 lineages) - Base lineages (9), Subraces (4)
- ✅ Classes (12 classes) - Full progression tables (levels 1-20)

**Remaining Work:**
- v0.9.3: Text parser refactor (Phase 3 - remaining 8 complex parsers)
- v0.10.0: Conditions dataset (~15-20 conditions)
- v0.11.0: Features dataset (class/racial features with cross-references)
- v0.12.0: Rules dataset (core mechanics, variant rules)
- v0.13.0: Quality & Polish (final cleanup, cross-dataset validation)
- v1.0.0: First stable release with all datasets

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

## **v0.5.0 — Equipment Dataset** ✅ COMPLETE **[DATA]**

**Released:** October 2025
**Consumer Impact:** NEW - 111 equipment items added

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

## **v0.5.1 — Action Parsing & Ability Modifiers** ✅ COMPLETE **[DATA]**

**Released:** November 1, 2025
**Consumer Impact:** NEW - Structured combat fields (attack_type, to_hit, damage, ability modifiers)

**Goal:** Deliver HIGH priority Blackmoor requests for structured combat data.

**Delivered**

* **Action Parsing (472/884 actions)**
  - New parse_actions.py module with regex-based field extraction
  - Fields: attack_type, to_hit, reach/range, damage (average/dice/type), saving_throw
  - Applies to actions, legendary_actions, and reactions
  - Preserves original text field for fallback
  - 14 comprehensive tests (all passing)

* **Ability Score Modifiers**
  - Calculated (score - 10) // 2 for all abilities
  - Added *_modifier fields alongside base scores
  - Example: {"strength": 21, "strength_modifier": 5}
  - 5 tests (all passing)

* **Schema Version Management**
  - Semantic versioning: MAJOR.MINOR.PATCH
  - v1.1.0 → v1.2.0 (MINOR bump for additive changes)
  - Synchronized all schemas (monster, equipment, spell)
  - Test suite: 82/83 passing (1 pre-existing failure)

**Benefits for Blackmoor:**
- Direct access to combat stats without text parsing
- Enables automated attack resolution
- Supports damage calculation in VTT combat engine
- Structured saving throw data for DC checks

**Quality Metrics:**
- Coverage: 472/884 actions (53.4%) with attack_type parsing
- Remaining 47% are non-attack actions (Multiattack, utility abilities)
- All new features have comprehensive test coverage
- Fixtures updated to current extraction format

---

## **v0.5.2 — Quality & Stability Release** ✅ COMPLETE **[INFRASTRUCTURE]**

**Released:** November 1, 2025
**Consumer Impact:** NONE - Same data as v0.5.1, internal improvements only

**Goal:** Internal quality improvements and infrastructure hardening (no customer-facing data changes).

**What's in v0.5.2 for Blackmoor:**
- **No new data fields** - This is a quality/infrastructure release
- **Same monster and equipment data** as v0.5.1
- **Enhanced reliability** - Better version tracking and test coverage
- **Preparation for spells** - Infrastructure ready for v0.6.0

**For Consumers:**
- Output files are identical to v0.5.1 (monsters.json, equipment.json)
- Schema version unchanged (1.2.0)
- Package version updated to 0.5.2 in `generated_by` metadata

**Technical Improvements (Internal)**

* **Version Management Consolidation**
  - Created `constants.py` for shared version constants
  - Three independent versions: `__version__` (0.5.2), `EXTRACTOR_VERSION` (0.3.0), `SCHEMA_VERSION` (1.2.0)
  - Removed redundant version tracking
  - Clear documentation on when each version changes

* **Test Infrastructure**
  - Split tests into unit (90) vs package validation (2)
  - Faster CI (no build required for unit tests)
  - 92/92 tests passing
  - Tests now validate against constants (never get out of sync)

**Summary for Blackmoor:**
This is a **maintenance release** with no new features or data changes. Safe to skip if you're already on v0.5.1. Recommend waiting for v0.6.0 (Spells) for the next major update.

---

## **v0.5.3 — Package Structure Refactoring** ✅ COMPLETE **[INFRASTRUCTURE]**

**Released:** November 1, 2025
**Consumer Impact:** BREAKING - File paths changed (simple migration)

**Goal:** Align package structure with standard data package conventions and simplify Blackmoor integration.

**What Changed:**
- **Data files moved to package root** - No more nested `data/` subdirectory
- **Simpler paths** - `monsters.json` instead of `data/monsters.json`
- **Supporting files stay organized** - `schemas/` and `docs/` remain in subdirectories

**Package Structure (Before → After):**
```
Before (v0.5.2):              After (v0.5.3):
dist/srd_5_1/                 dist/srd_5_1/
├── data/                     ├── monsters.json      ← At root
│   ├── monsters.json         ├── equipment.json
│   ├── equipment.json        ├── index.json
│   ├── index.json            ├── meta.json
│   └── meta.json             ├── README.md
├── README.md                 ├── build_report.json
├── build_report.json         ├── schemas/
├── schemas/                  └── docs/
└── docs/
```

**Migration for Blackmoor:**
```python
# Old (v0.5.2):
monsters_path = ruleset_dir / "data" / "data" / "monsters.json"  # Double nesting!

# New (v0.5.3):
monsters_path = ruleset_dir / "data" / "monsters.json"  # Clean!
```

**Why This Change?**
1. **Standard convention** - Most data packages put data at root, metadata in subdirs
2. **Simpler integration** - One less directory level to navigate
3. **Clearer structure** - Immediately visible what files are the actual data
4. **Customer feedback** - Blackmoor team requested this alignment

**Technical Details:**
- All 92 tests passing with new structure
- Validation updated: `python -m srd_builder.validate --ruleset srd_5_1`
- Documentation updated (README, BUNDLE_README)
- meta.json file paths updated (no `data/` prefix)

**Summary for Blackmoor:**
This is a **breaking change** but migration is straightforward - just remove one `"data"` from your path construction. The data content is identical to v0.5.2. Recommend updating to v0.5.3 before v0.6.0 (Spells) to get the cleaner structure.

---

## **v0.5.5 — Table Metadata Discovery (Phase 0.5)** ✅ MERGED INTO v0.7.0

**Original Goal:** Build infrastructure for systematic table discovery to prevent per-table debugging cycles.

**Status:** **MERGED** — This work is now part of v0.7.0 (Reference Tables + Table Indexer)

**Why the merge?**
- v0.7.0 already requires building table extraction infrastructure
- Building table discovery at same time is efficient (one-time investment)
- Prevents building reference tables with heuristics, then rebuilding with metadata later
- Table indexer provides validation baseline for all future table work

**Original Problem:** Current heuristic approach works but doesn't scale
- Equipment armor subcategory fix used name-based inference (pragmatic but brittle)
- PDF table layouts are complex, context tracking unreliable
- Each new table requires custom debugging and fixes
- No validation capability ("did we extract all tables?")

**Solution (Now in v0.7.0):** `table_indexer.py` + `table_metadata.json`
```python
table_indexer.discover_tables() → table_metadata.json
{
  "tables": [
    {
      "id": "equipment_armor",
      "pages": [63, 64],
      "headers": ["Armor", "Cost", "Armor Class (AC)", "Strength", "Stealth", "Weight"],
      "row_count": 14,
      "bbox": [x, y, width, height],
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
- Enables quality metrics: "extracted 12/12 expected tables"

**See:** v0.7.0 for full implementation details

---

## **v0.6.2 — Spells Dataset** ✅ COMPLETE **[DATA]**

**Released:** November 2025
**Priority:** HIGH (Blackmoor customer request)
**Consumer Impact:** NEW - 319 spells with structured fields

**Goal:** Extract and structure D&D 5e spells from SRD 5.1.

**Why Spells Next?**
- D&D gameplay is spell-heavy for casters
- Complements monsters (many have spellcasting) and equipment
- Critical for character actions in combat/narrative systems
- Different extraction pattern than tables (validates architecture)

**Scope**
- Estimated ~300-400 spells in SRD 5.1
- Schema proposal: docs/external/blackmoor/spell_schema_proposal.md
- Fields: level, school, casting_time, range, components, duration, concentration
- Structured data: damage, healing, saving_throws, area_of_effect
- Index by: level, school, name

**Schema Approach (v1.2.0 → v1.3.0)**
- MINOR bump for additive changes (new spell.schema.json)
- Core fields: id, simple_name, name, level, school, text
- Optional fields: damage, healing, save, attack, area_of_effect
- Components: {verbal: bool, somatic: bool, material: bool, material_description: string}
- Preserve raw text for complex spells

**Implementation Pattern**
```
extract_spells.py → parse_spells.py → postprocess.py → indexer.py
```

**Success Criteria**
- [x] ~300+ spells extracted (319 total)
- [x] Schema v1.3.0 validated
- [x] Index by level, school, name
- [x] Test coverage: extraction, parsing, validation
- [x] Data quality validation (empty text detection, duplicate detection)

**What Shipped:**
- 319 spells with structured fields (level, school, casting, components, effects)
- Effects parsing: damage (472/884 actions), healing, saves, attacks, area
- Scaling: slot-based upcast and character-level cantrip scaling
- Fixed 7 spells with empty text (multi-page spell description edge case)
- Equipment deduplication (111→106 items, removed duplicate pot-iron)
- Container capacity data for 8 containers with `container: true` property
- Data quality validation catches empty text and duplicate IDs

---

## **v0.6.3 — Path Fix** ✅ COMPLETE **[BUGFIX]**

**Released:** November 2025
**Priority:** LOW (cosmetic fix)
**Consumer Impact:** Minor - corrected relative path in metadata

**Goal:** Fix incorrect `build_report.json` path reference in output metadata.

**What Shipped:**
- Fixed `build_report` path from `../build_report.json` to `./build_report.json`
- All output files now correctly reference build report in same directory
- Updated test expectations and fixtures to match corrected path

---

## **v0.6.4 — Parsing Gap Fixes** ✅ COMPLETE **[DATA QUALITY]**

**Released:** November 2025
**Priority:** HIGH
**Consumer Impact:** Significant improvements to spell data quality

**Goal:** Close critical parsing gaps identified in v0.6.3 confidence assessment.

**What Shipped:**

1. **Ritual flag extraction** (CRITICAL BUG FIX) ✅
   - Fixed: 0% → 9% (29 ritual spells)
   - Root cause: Parser checked wrong field (`casting_time` vs `level_and_school`)
   - Examples: Detect Magic, Identify, Find Familiar, Alarm, Commune
   - Commit: 3049c70

2. **Area-of-effect parsing** (NEW FEATURE) ✅
   - Implemented: 0% → 17% (55 spells with structured area data)
   - Handles PDF spacing artifacts ("20- foot- radius sphere")
   - Two patterns: standard shapes + line spells
   - Examples: Fireball (20-foot sphere), Burning Hands (15-foot cone), Lightning Bolt (100-foot line)
   - Commit: 3049c70

3. **Healing effects** (NEW FEATURE) ✅
   - Implemented: 0% → 2% (5 dice-based healing spells)
   - Pattern: "regains hit points equal to XdX"
   - Schema note: Fixed-amount healing excluded (requires dice pattern)
   - Examples: Cure Wounds (1d8), Healing Word (1d4), Mass Cure Wounds (3d8)
   - Commit: 37927ae

4. **Attack roll effects** (NEW FEATURE) ✅
   - Implemented: 0% → 6% (19 attack spells)
   - Schema-compliant types: `melee_spell`, `ranged_spell`
   - Examples: Fire Bolt, Chill Touch (ranged), Shocking Grasp, Contagion (melee)
   - Commit: 37927ae

5. **Equipment category** (NON-ISSUE) ✅
   - Verified: "gear" is correct primary category (schema-compliant)
   - Design note: "adventuring_gear" would be subcategory/property/alias if needed
   - All equipment tests passing

**Impact:**
- Ritual flag: 0% → 100% (29 spells, manually verified v0.8.2)
- Effects coverage: 44% → 52% (+8 percentage points, 140→166 spells)
- All 113 tests passing
- Schemas remain at v1.3.0 (no breaking changes)

**Why v0.6.4 (not v0.7.0)?**
These are quality improvements to existing v0.6.x spell/equipment data, not new datasets. Keeping within v0.6.x patch series maintains semantic versioning and allows v0.7.0 to remain Classes & Lineages as originally planned.

---

## **v0.6.5 — Version Management Tooling** ✅ COMPLETE **[TOOLING]**

**Released:** November 2025
**Priority:** LOW (developer experience improvement)
**Consumer Impact:** None (internal tooling only)

**Goal:** Automate version bump workflow to eliminate manual errors.

**What Shipped:**
- `scripts/bump_version.py` - Automated version management script
  - Updates `__version__` in `__init__.py`
  - Regenerates all test fixtures with new version + schema version
  - Updates README.md build pipeline version
  - Runs full test suite for verification
  - Creates detailed git commit with all changes

**Usage:**
```bash
python scripts/bump_version.py 0.6.6
make bump-version VERSION=0.6.6
python scripts/bump_version.py 0.7.0 --no-commit  # Preview only
```

**Benefits:**
- Eliminates manual fixture regeneration steps
- Ensures version consistency across 5+ files
- Catches missing ROADMAP.md documentation via test
- Standardizes commit messages
- Reduces release preparation time

---

## **v0.7.0 — Reference Tables Dataset + Table Indexer** **[DATA + INFRASTRUCTURE]** ✅ **COMPLETE**

**Status:** SHIPPED - Reference tables extracted and indexed
**Priority:** HIGH (foundational for other datasets + prevents per-table debugging)
**Effort:** Medium (includes deferred v0.5.5 table metadata work)
**Consumer Impact:** NEW - ~10-15 reference tables + validation infrastructure

**Goal:** Extract reusable reference tables from SRD 5.1 AND build systematic table discovery infrastructure.

**Why Tables + Indexer Together?**
- Already building table extraction - perfect time to build it right
- Needed by Classes (level progression, proficiency bonus)
- Needed by Spells (spell slots by level)
- Needed by general gameplay (services, travel pace, carrying capacity)
- Prevents future per-table debugging cycles (original v0.5.5 motivation)
- Table metadata enables validation: "Did we extract all expected tables?"
- Validates our table extraction infrastructure for public consumption

**Scope - Part 1: Table Indexer (Infrastructure)**
- **NEW:** `table_indexer.py` - Scan entire PDF for tables
- Generate `table_metadata.json` with comprehensive metadata:
  - Table locations (pages, bounding boxes)
  - Headers and column count
  - Row counts (actual vs expected)
  - Section context (chapter, subsection)
- Validation baseline for extraction quality
- Prevents "did we miss any tables?" uncertainty

**Scope - Part 2: Reference Tables (Consumer Data)**
- **HIGH Priority:** ~12 core tables (documented in `scripts/table_targets.py`)
  - Ability scores and modifiers
  - Proficiency bonus by level
  - Experience points by CR
  - Spell slots by class level
  - Cantrip damage by level
  - Travel pace
  - Services, food/drink/lodging
  - Creature size categories
- **MEDIUM/LOW:** Deferred if time-boxed
  - Carrying capacity, lifestyle expenses, condition effects

**Schema (table.schema.json)**
```json
{
  "id": "table:experience_by_cr",
  "simple_name": "experience_by_cr",
  "name": "Experience Points by Challenge Rating",
  "summary": "XP rewards for defeating monsters",
  "columns": [
    {"name": "CR", "type": "string"},
    {"name": "XP", "type": "integer"}
  ],
  "rows": [
    ["0", 10],
    ["1/8", 25],
    ["1", 200]
  ],
  "page": 57,
  "category": "combat"
}
```

**Implementation:**
- `table_indexer.py` - PDF-wide table discovery (uses PyMuPDF find_tables())
- `extract_tables.py` - Extract specific reference tables (uses metadata)
- `parse_tables.py` - Normalize to schema (IDs, types, summaries)
- `scripts/table_targets.py` - Target list with priorities

**Benefits of Combined Approach:**
- One-time investment in table infrastructure pays dividends
- Metadata enables quality validation for all future table work
- Equipment extraction can later use same metadata for validation
- Classes/features datasets will benefit from proven table patterns

---

## **v0.8.0 — Classes & Lineages** **[DATA]** ✅ **COMPLETE**

**Status:** SHIPPED - Lineages extracted (13 entries), Classes deferred to v0.8.2
**Goal:** Extract character creation content.

**Scope:**
- Classes (complex with level progression tables) - **Pages 8-55**
- Lineages/Races (character creation features) - **Pages 3-7**
- **Terminology aliases** (add `terminology.aliases` to meta.json: `{"races": "lineages"}`)

**Priority:** MEDIUM - Important for character creation, but NPCs use monster stats

**Why Classes After Tables?**
- Core D&D content for character building
- Complex extraction (level progression tables)
- **Depends on v0.7.0 tables** (proficiency bonus, spell slots)
- Validates table extraction architecture
- Complements existing monster, equipment, and spell data
- Terminology aliases enable backward-compatible naming

**Lineage/Race Terminology:**
- Output file: `lineages.json`
- Field namespace: `lineage:*` (e.g., `lineage:dwarf`)
- meta.json will include: `"terminology": {"aliases": {"races": "lineages"}}`
- Maintains modern 5e terminology while enabling discoverability

**Classes Details:**
- 12 classes: Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard
- Output file: `classes.json`
- Field namespace: `class:*` (e.g., `class:fighter`)
- Includes: hit die, proficiencies, features, subclasses, level progression

---

## **v0.8.1 — Comprehensive Alias System & PDF Metadata** **[QUALITY]** ✅ **COMPLETE**

**Status:** SHIPPED - Three-level alias system, PDF metadata extraction, auto-generated data dictionary
**Goal:** Enhance discoverability and eliminate hardcoded metadata.

**Scope:
- **Three-level alias pattern:**
  - Index-level: Terminology aliases in `index.json` (`{"races": "lineages", "race": "lineage"}`)
  - Entity-level: Optional `aliases` field in all schemas (equipment, lineage, spell, monster, table)
  - Indexer-level: Automatic alias expansion in `by_name` indexes
- **PDF metadata extraction:**
  - Extract version, license, URLs, attribution from PDF page 1
  - Replace hardcoded values in meta.json with authoritative PDF data
  - New module: `extract_pdf_metadata.py`
- **Auto-generated data dictionary:**
  - `generate_data_dictionary.py` creates `DATA_DICTIONARY.md` from schemas
  - Swagger/OpenAPI-style field reference
  - Eliminates manual documentation maintenance

**Why This Matters:**
- **Discoverability:** Consumers can search by alternative names ("flask", "tankard") → `flask_or_tankard`
- **Backward compatibility:** Old code using "race" still works via index-level aliases
- **Authoritative metadata:** PDF is source of truth, not hardcoded values
- **Maintainability:** Schema changes automatically update documentation

**Implementation Details:**
- Index-level aliases enable categorical mappings (races → lineages)
- Entity-level aliases stored in data, automatically indexed
- `by_name` indexes include all aliases for transparent lookups
- PDF extraction runs during build, falls back to constants if unavailable
- Data dictionary auto-generated from JSON schemas with full validation rules

**Documentation:**
- `docs/ARCHITECTURE.md` - Added alias system architecture section
- `docs/SCHEMAS.md` - Added aliases field documentation
- `docs/BUNDLE_README.md` - Updated with alias usage examples
- `docs/DATA_DICTIONARY.md` - Auto-generated field reference (Swagger-style)

---

## **v0.8.2 — Classes Dataset** **[DATA]** ✅ **COMPLETE**

**Status:** SHIPPED - All 12 classes implemented with progression data
**Priority:** HIGH - Needed for Blackmoor distribution
**Effort:** Medium
**Consumer Impact:** NEW - 12 character classes with full progression

**Goal:** Complete character creation datasets with classes implementation.

**Scope:**
- 12 classes: Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, Wizard
- Output file: `classes.json`
- Field namespace: `class:*` (e.g., `class:fighter`)
- Includes: hit die, proficiencies, features, subclasses, level progression
- Table references: Each class references progression table + proficiency_bonus + spell slots (if applicable)

**Implementation:**
- `schemas/class.schema.json` v1.3.0 - Matches schema standards with aliases support
- `src/srd_builder/class_targets.py` - Canonical class data from pages 8-55
- `src/srd_builder/parse_classes.py` - Pure parsing (no I/O)
- `src/srd_builder/indexer.py` - Added `build_class_index()` with by_name, by_hit_die, by_primary_ability
- `src/srd_builder/build.py` - Integrated classes into build pipeline

**Deferred to Future:**
- Class progression tables extraction (12 tables, pages 8-55)
- Currently class progression data is in `progression` field as simplified text
- Full table extraction documented in `docs/PARKING_LOT.md`

**Meta.json Updates:**
- `page_index.classes`: Pages 8-55
- `page_index.lineages`: Pages 3-7 (fixed - was missing)
- `files.classes`: "classes.json"
- `extraction_status.classes`: "complete"

---

## **v0.8.3 — Equipment Cleanup** **[QUALITY]** ✅ **COMPLETE**

**Status:** SHIPPED - Equipment properties cleaned, proficiency field added
**Priority:** HIGH - Data quality improvement for Blackmoor
**Effort:** Low
**Consumer Impact:** IMPROVED - Cleaner data, better weapon indexing

**Goal:** Clean equipment data and add weapon proficiency field.

**Changes:**
1. **Clean Properties Array**
   - Stripped embedded data from properties: `"versatile (1d10)"` → `"versatile"`
   - Fixed Unicode dash issues: `"two-­‐handed"` → `"two_handed"`
   - Extracted embedded data to structured fields before cleaning

2. **Added Proficiency Field**
   - New field: `proficiency: "simple" | "martial"` for weapons
   - Section-based extraction with name-based fallback
   - Independent from `weapon_type` field for flexible querying

3. **Updated Indexes**
   - Added `by_proficiency` index: simple (7), martial (11)
   - Added `by_weapon_type` index: melee (7), ranged (8)
   - Enables queries: "all simple weapons", "all martial melee weapons"

4. **Data Integrity**
   - `versatile_damage` extracted before property cleaning
   - `range` extracted before property cleaning
   - All structured fields preserved

**Files Modified:**
- `src/srd_builder/parse_equipment.py` - Property cleaning, proficiency extraction
- `src/srd_builder/extract_equipment.py` - Fixed weapon subcategory markers
- `src/srd_builder/indexer.py` - Added proficiency and weapon_type indexes
- `src/srd_builder/postprocess.py` - Added proficiency to optional fields
- `tests/test_parse_equipment.py` - Updated for clean properties

**Schema:** 1.3.0 (no bump - additive changes only, pre-handoff)

---

## **v0.8.4 — Character Creation Blockers** **[QUALITY]** ✅ **COMPLETE**

**Released:** November 3, 2025
**Status:** SHIPPED - All character creation blockers resolved
**Priority:** CRITICAL - Blocked character creation entirely
**Effort:** Low (small extraction improvements)
**Consumer Impact:** CRITICAL - Unblocks character creation flow

**Goal:** Add missing critical fields to lineages, classes, and spells to unblock Blackmoor's character creation.

**Blackmoor Feedback:**
Real-world integration testing revealed 3 critical gaps not in TODO.md:
1. Lineages missing ability score increases (Human has no +1 all stats)
2. Classes missing primary ability and saving throw proficiencies
3. Spells missing range field (blocks ranged spell attacks)

**Delivered:**

1. **Lineage Ability Modifiers** ✅
   - Renamed: `ability_increases` → `ability_modifiers` (future-proofed for 3.5e negative values)
   - All 13 lineages updated with modifiers
   - Example: Human → `ability_modifiers: {strength:1, dexterity:1, constitution:1, intelligence:1, wisdom:1, charisma:1}`
   - Example: Dwarf → `ability_modifiers: {constitution:2}`
   - Impact: Enables character creation, supports future editions

2. **Class Saving Throw Proficiencies** ✅
   - Renamed: `saves` → `saving_throw_proficiencies` (clearer naming per Blackmoor)
   - Normalized: `["Str","Dex"]` → `["strength","dexterity"]` (consistent with rest of schema)
   - All 12 classes updated
   - Example: Fighter → `primary_abilities: ["strength","dexterity"]`, `saving_throw_proficiencies: ["strength","constitution"]`
   - Impact: Enables character sheet generation, multiclass prerequisites

3. **Subrace Parent Lineage Links** ✅
   - Added `parent_lineage` reference field to subraces
   - 4 subraces link to parents: Hill Dwarf → `lineage:dwarf`, High Elf → `lineage:elf`, etc.
   - Impact: Enables trait inheritance resolution

4. **Spell Range Field** ✅
   - Complete range structure redesign: `{type, distance?, area?}`
   - All 319 spells with range data (183 ranged, 68 self, 65 touch, 14 with area)
   - Handles complex ranges: "Self (15-foot cone)" → `{type:"self", area:{shape:"cone", size:{value:15, unit:"feet"}}}`
   - Fixed Unicode dash handling in PDF extraction
   - Impact: Enables ranged spell attacks, spell targeting, VTT integration

**Quality Metrics:**
- ✅ All 6 datasets production-ready (5-star for Blackmoor)
- ✅ 114 tests passing
- ✅ Zero lineages without ability_modifiers
- ✅ All subraces have parent_lineage
- ✅ All classes have saving_throw_proficiencies
- ✅ Zero spells with null range

**Breaking Changes:**
- Schema: 1.3.0 → 1.4.0
- Lineages: `ability_increases` → `ability_modifiers`, added `parent_lineage`
- Classes: `saves` → `saving_throw_proficiencies`, lowercase ability names
- Spells: Range structure completely redesigned

---

## **v0.8.5 — Spell Enhancements** **[QUALITY]** ✅ **COMPLETE**

**Released:** November 3, 2025
**Status:** SHIPPED - Spell mechanics polish complete
**Priority:** HIGH - Needed for spellcasting gameplay
**Effort:** Medium
**Consumer Impact:** IMPROVED - Complete spell mechanics

**Goal:** Complete spell mechanics coverage for healing, area of effect, and edge cases.

**Delivered:**

1. **Spell Healing Coverage** ✅
   - Coverage: 0% → 100% (10/10 healing spells)
   - Three pattern types implemented:
     - **Dice-based:** `{dice: "1d8"}` - Cure Wounds, Healing Word, Mass Cure Wounds, Mass Healing Word, Prayer of Healing
     - **Dice with modifier:** `{dice: "4d8+15"}` - Regenerate
     - **Fixed amount:** `{amount: 70}` - Heal (70 HP), Mass Heal (700 HP)
     - **Conditional:** `{condition: "half the amount of necrotic damage dealt"}` - Vampiric Touch, Wish
   - Schema: Updated to support three healing types via oneOf (dice, amount, condition)
   - Captures all healing mechanics including full restoration and conditional healing

2. **Area of Effect Improvements** ✅
   - Coverage: 17.2% → 24.8% (+43% improvement, 55 → 79 spells)
   - Five new patterns implemented:
     - Cylinder with height: "10-foot-radius, 40-foot-high cylinder"
     - Cylinder reversed: "10 feet tall with a 60-foot radius"
     - Diameter: "5-foot-diameter sphere"
     - Radius-only (defaults to sphere): "10-foot radius"
     - Standard shapes: "X-foot radius sphere/cone/cube/cylinder"
   - Breakdown by shape: sphere (41), cube (20), line (8), cone (5), cylinder (5)
   - Examples: Flame Strike, Antilife Shell, Call Lightning, Flaming Sphere all captured

3. **Spell Range Field** ✅
   - Coverage: 100% (319/319 spells)
   - Already complete from v0.8.4
   - Location note: Range data stored in `spell.casting.range` object
   - Structure: `casting: {time, range, duration, concentration, ritual}`
   - Design rationale: All casting mechanics grouped together (semantically logical)
   - Types: ranged (183), self (68), touch (65), sight (2), unlimited (1)

**Quality Metrics:**
- ✅ 10/10 healing spells captured (100%)
- ✅ 79/319 spells with area data (24.8%)
- ✅ 319/319 spells with range data (100%)
- ✅ 114 tests passing
- ✅ 16 new tests added for healing/AOE patterns

**Documentation Notes:**
- **Range field location:** `spell.casting.range` (nested in casting object)
  - Groups all casting mechanics: time, range, duration, concentration, ritual
  - Design is intentional and semantically logical
  - Consumer tip: Access via `spell["casting"]["range"]` not `spell["range"]`

**Conditions Notes:**
- Created `docs/CONDITIONS_NOTES.md` for future v0.10.0 work
- Identified condition-like spell effects: Beacon of Hope (buff), Chill Touch (debuff)
- Deferred to Conditions dataset for proper cross-referencing

**Schema:** 1.4.0 (healing schema updated with oneOf for three types)

---

## **v0.8.6 — Spell Duration Restructure** **[QUALITY]** ✅ **COMPLETE**

**Released:** November 4, 2025
**Status:** SHIPPED - Duration field restructured per Blackmoor feedback
**Priority:** MEDIUM - API discoverability improvement
**Effort:** Low (schema + parser change)
**Consumer Impact:** IMPROVED - Concentration more discoverable

**Goal:** Make concentration requirements more discoverable by restructuring duration field.

**Blackmoor Feedback:**
- Concentration was buried: `spell.casting.concentration` separate from duration
- Proposed: Move duration to top level with structured object including concentration

**Delivered:**

1. **Duration Field Restructure** ✅
   - **Before:** `casting.duration` (string) + `casting.concentration` (boolean)
   - **After:** `duration` (object at top level with `requires_concentration` + `length`)
   - Structure: `{requires_concentration: boolean, length: string}`
   - Example (no concentration): `{requires_concentration: false, length: "instantaneous"}`
   - Example (with concentration): `{requires_concentration: true, length: "up to 1 minute"}`
   - Impact: Concentration is now semantically part of duration, easier to discover

2. **Schema Updates** ✅
   - Removed: `casting.concentration` field
   - Removed: `casting.duration` from casting object
   - Added: Top-level `duration` object with `requires_concentration` and `length` properties
   - Schema version: 1.4.0 → 1.5.0

3. **Parser Updates** ✅
   - `_parse_duration()` now returns structured object instead of tuple
   - Duration output at spell top level instead of nested in casting
   - All 319 spells updated with new structure

**Quality Metrics:**
- ✅ 319/319 spells with new duration structure
- ✅ 122/319 spells require concentration (38.2%)
- ✅ All tests passing (30 parse_spells tests)

**Breaking Changes:**
- Schema: 1.4.0 → 1.5.0
- Spells: Duration moved from `casting.duration` to top-level `duration` object
- Spells: Removed `casting.concentration` field (now `duration.requires_concentration`)

**Consumer Migration:**
```javascript
// Before (v0.8.5)
const duration = spell.casting.duration;  // "up to 1 minute"
const needsConcentration = spell.casting.concentration;  // true

// After (v0.8.6)
const duration = spell.duration.length;  // "up to 1 minute"
const needsConcentration = spell.duration.requires_concentration;  // true
```

---

## **v0.9.0 — Text-Based Table Extraction** **[INFRASTRUCTURE + DATA]** ✅ **COMPLETE**

**Released:** November 4, 2025
**Status:** SHIPPED - Coordinate-based extraction breakthrough
**Priority:** HIGH - Unlocked equipment tables
**Effort:** Medium (new extraction method + infrastructure)
**Consumer Impact:** NEW - 3 equipment tables (26 total, up from 23)

**Goal:** Build text-based table extraction for tables without grid borders, expand equipment coverage.

### Phase 1: Infrastructure Refactor ✅

**Problem Statement:**
- extract_tables.py grew to 1508 lines with massive duplication
- 26 nearly identical extraction methods (one per table)
- Hardcoded table data mixed with extraction logic
- Adding new tables required copy-pasting entire methods

**Problem Statement:**
- extract_tables.py grew to 1508 lines with massive duplication
- 26 nearly identical extraction methods (one per table)
- Hardcoded table data mixed with extraction logic
- Adding new tables required copy-pasting entire methods

**Delivered:**

1. **Modular Architecture** ✅
   - Created `table_extraction/` package with 4 focused modules
   - `__init__.py` - Public API (9 lines)
   - `patterns.py` - Unified extraction engine (~100 lines)
   - `reference_data.py` - All table configurations (690 lines)
   - `extractor.py` - Routing & PyMuPDF integration (~230 lines)

2. **Unified Extraction Engine** ✅
   - Replaced 26 duplicate methods with single `extract_by_config()` function
   - Data-driven approach: config structure determines extraction behavior
   - Checks for "rows" (static data), "formula" (calculated), or "data" (lookup)
   - Example: Ability scores use formula `lambda score: (score - 10) // 2`

3. **Organized Reference Data** ✅
   - `CALCULATED_TABLES` - 3 formula/lookup tables (ability scores, proficiency, carrying capacity)
   - `REFERENCE_TABLES` - 5 static tables (CR/XP, spell slots, cantrip damage, travel pace, creature size)
   - `PRICING_TABLES` - 3 pricing tables (food/lodging, services, lifestyle)
   - `CLASS_PROGRESSIONS` - 12 class tables (all D&D classes, 20 levels each)
   - `get_table_data()` - Unified lookup with fallback chain

4. **Archived Old Code** ✅
   - Moved extract_tables.py → archived/extract_tables_v0.7.0.py
   - Added comprehensive header explaining refactor

**Quality Metrics:**
- ✅ Code reduced: 1508 lines → ~850 lines (50% reduction)
- ✅ Methods reduced: 26 extraction methods → 1 unified function (96% reduction)
- ✅ All 23 tables extract correctly (data integrity verified)
- ✅ Same output format (backward compatible)
- ✅ All tests passing

**Impact:**
- **Maintainability:** 50% less code to maintain
- **Extensibility:** Adding tables now requires config dict only, no new code
- **Clarity:** Clean separation between extraction logic and table data
- **Foundation:** Ready for v0.10.0+ expansion

**Files Modified:**
- Created: `src/srd_builder/table_extraction/__init__.py`
- Created: `src/srd_builder/table_extraction/patterns.py`
- Created: `src/srd_builder/table_extraction/reference_data.py`
- Created: `src/srd_builder/table_extraction/extractor.py`
- Updated: `src/srd_builder/build.py` (changed imports)
- Archived: `src/srd_builder/extract_tables.py` → `archived/extract_tables_v0.7.0.py`

**Note on condition_effects:**
- Added to TARGET_TABLES as placeholder for v0.10.0 Conditions Dataset
- Currently fails extraction (expected - no config yet)
- Will be implemented in v0.10.0

### Phase 2: Text-Based Table Extraction ✅

**The Breakthrough:** Coordinate-based extraction for tables without grid borders

**Problem:**
- Equipment tables (armor, weapons, exchange rates) have no visual grid lines
- PyMuPDF's table detection: 1/15 tables detected (6.7% success rate)
- Previous attempts relied on heuristics and context tracking (fragile)

**Solution:**
- PyMuPDF's `get_text("words")` returns `(x0, y0, x1, y1, text, ...)` tuples
- **Key insight:** Words at same Y-coordinate = same row, sort by X = column order
- No grid borders needed - spatial layout IS the structure

**Delivered:**

1. **Universal Extraction Engine** ✅
   - `_extract_rows_by_coordinate(pdf_path, pages)` - Core engine
   - Groups words by Y-coordinate (rows) with 2-pixel tolerance
   - Sorts by X-coordinate (columns) for left-to-right order
   - Returns list of word lists for all rows

2. **Table-Specific Parsers** ✅
   - `parse_armor_table()` - 13 armor items (pages 63-64)
   - `parse_weapons_table()` - 37 weapons (pages 65-66)
   - `parse_exchange_rates_table()` - 5 currencies (page 62)
   - Each parser filters rows and maps columns to structured data

3. **Integration** ✅
   - `extractor.py` - Added `_extract_text_parsed()` method
   - `reference_data.py` - Added `TEXT_PARSED_TABLES` config
   - `table_targets.py` - Added 3 equipment table entries
   - Full build integration via existing pipeline

4. **Edge Cases Handled** ✅
   - Armor: Trailing "—" symbols, "Str 13" requirements
   - Weapons: Sling (no weight), Blowgun ("1 piercing"), Net (no damage)
   - Exchange rates: Combined columns ("Copper" + "(cp)")
   - Headers: Fixed double-nesting bug (headers returned as dicts vs strings)

**Quality Metrics:**
- ✅ 100% extraction accuracy for text-embedded tables (vs 7% with auto-detect)
- ✅ 13/13 armor items extracted correctly
- ✅ 37/37 weapons extracted correctly (including edge cases)
- ✅ 5/5 currencies extracted correctly
- ✅ All validation warnings in place (expected row counts)
- ✅ Zero fabrication - all data from PDF

**Code Quality:**
- Created: `src/srd_builder/table_extraction/text_table_parser.py` (345 lines)
- Removed: 82 lines of dead code (unused generic parser)
- Integration: Clean separation via extractor routing
- Tests: Build verification, data accuracy checks

**Architecture:**
```
PDF Pages → _extract_rows_by_coordinate() → All text rows with coordinates
              ↓
         Table-Specific Parsers (filter + structure)
              ↓
         extractor.py _extract_text_parsed() → RawTable
              ↓
         parse_single_table() → Normalized schema
              ↓
         dist/tables.json (26 tables)
```

**Lessons Learned:**
1. Coordinate-based extraction works where visual detection fails
2. Specific parsers more reliable than generic config-driven approach (for now)
3. PDF as authoritative source is non-negotiable
4. Validation warnings catch extraction issues early
5. Edge cases (Sling, Blowgun, Net) require explicit handling

**Future Work (v0.9.1+):**
- Apply pattern to remaining equipment tables (donning/doffing, adventure gear, mounts, food/lodging)
- Refactor to config-driven pattern once proven at scale
- Extract equipment descriptions (currently table-only)

---

## **v0.9.1 — Equipment Tables Expansion** **[DATA]** ✅ **COMPLETE**

**Released:** November 4, 2025
**Status:** SHIPPED - Adventure gear, tools, containers extracted
**Priority:** HIGH - Complete equipment reference tables
**Effort:** Medium
**Consumer Impact:** NEW - 7 equipment tables (30 → 33 tables total)

**Goal:** Apply coordinate-based extraction to remaining equipment tables.

**Delivered:**

1. **Adventure Gear Table** ✅
   - 99 items + 4 category sections (Common Goods, Equipment Packs, Clothing, Magic)
   - Pages 66-68, multi-page extraction
   - Weight parsing with optional units, cost parsing with gp/sp/cp
   - Category metadata preserved in headers array

2. **Donning and Doffing Armor Table** ✅
   - 4 armor categories (Light, Medium, Heavy, Shield)
   - Page 68, single column right side
   - Time-based columns (Don, Doff)

3. **Container Capacity Table** ✅
   - 13 containers with capacity data
   - Pages 69-70, two-page extraction
   - Capacity parsing with units (cubic feet, gallons)

**Quality Metrics:**
- ✅ 33 tables total (was 30)
- ✅ All 3 new tables extract correctly
- ✅ Adventure gear: 99 items + 4 categories ✓
- ✅ Donning/doffing: 4 armor types ✓
- ✅ Container capacity: 13 containers ✓
- ✅ Zero behavioral change for existing 30 tables

**Code Quality:**
- Extended text_table_parser.py with 3 new parser functions
- Multi-page extraction patterns refined
- Category metadata handling established
- All tests passing

---

## **v0.9.2 — Equipment Tables Complete** **[DATA]** ✅ **COMPLETE**

**Released:** November 4, 2025
**Status:** SHIPPED - All equipment/reference tables extracted
**Priority:** HIGH - Complete equipment section
**Effort:** Medium
**Consumer Impact:** NEW - 7 more tables (33 → 37 tables total)

**Goal:** Complete equipment section extraction (pages 62-74).

**Delivered:**

1. **Tools Table** ✅
   - 35 items + 3 category sections (Artisan's Tools, Gaming Sets, Musical Instruments)
   - Page 70, right column

2. **Mounts and Other Animals** ✅
   - 8 animals (camel, donkey, elephant, horse variants, mastiff, pony, warhorse)
   - Pages 71-72, multi-page extraction
   - 4-column layout: Item | Cost | Speed | Capacity

3. **Tack, Harness, and Drawn Vehicles** ✅
   - 14 items including saddle types (exotic, military, pack, riding)
   - Page 72, right column
   - Special logic for saddle subcategories: "Saddle, exotic" pattern

4. **Waterborne Vehicles** ✅
   - 6 vehicles (galley, keelboat, longship, rowboat, sailing ship, warship)
   - Page 72, left column

5. **Trade Goods** ✅
   - 13 commodity items (wheat, flour, chicken, cow, copper, etc.)
   - Page 72, bottom right

6. **Lifestyle Expenses** ✅
   - 7 lifestyle categories (wretched → aristocratic)
   - Pages 72-73, multi-page extraction

7. **Food, Drink, and Lodging** ✅
   - 19 items (ale, bread, cheese, inn stays, meals)
   - Pages 73-74, multi-page extraction

8. **Services** ✅
   - 7 service types (coach hire, messenger, spell casting, etc.)
   - Page 74, right column

**Quality Metrics:**
- ✅ 37 tables total (12 class progression + 25 equipment/reference)
- ✅ All 7 new tables extract correctly
- ✅ Equipment section pages 62-74 complete
- ✅ 111 equipment items across all tables
- ✅ Zero behavioral change for existing 30 tables

**Code Quality:**
- Extended text_table_parser.py with 7 new parser functions
- Multi-page extraction patterns proven at scale
- Saddle subcategory handling (special case)
- All tests passing

**Tagged:** v0.9.2-equipment-tables (known good state before refactor)

---

## **v0.9.3 — Text Parser Refactor** **[INFRASTRUCTURE]** 🔄 **IN PROGRESS**

**Released:** TBD
**Status:** IN PROGRESS - Phase 2 of 3 complete
**Priority:** MEDIUM - Code quality improvement
**Effort:** Medium
**Consumer Impact:** NONE - Zero behavioral change

**Goal:** Reduce duplication in text_table_parser.py through incremental refactoring.

**Progress:**

**Phase 1: Utilities Module** ✅ COMPLETE (commit dd4d091)
- Created `text_parser_utils.py` with 8 utility functions
- Functions: `group_words_by_y()`, `extract_region_rows()`, `find_currency_index()`, etc.
- Refactored `parse_trade_goods_table()` as proof-of-concept
- File baseline: 1386 lines

**Phase 2: Simple Parser Refactoring** ✅ COMPLETE (commit df8ba79)
- Refactored 5 parsers to use utilities:
  - `parse_services_table()`: 62→42 lines (-20)
  - `parse_waterborne_vehicles_table()`: 75→49 lines (-26)
  - `parse_lifestyle_expenses_table()`: 91→49 lines (-42)
  - `parse_food_drink_lodging_table()`: 94→50 lines (-44)
  - `parse_trade_goods_table()`: 58→40 lines (-18, from Phase 1)
- Added `extract_multipage_rows()` utility for spanning tables
- Total reduction: ~150 lines of duplication
- File size: 1386 → 1255 lines (-131 lines, -9.5%)
- All 37 tables validated with correct row counts

**Phase 3: Complex Parser Refactoring** 📋 NOT STARTED
- 8 remaining unrefactored parsers:
  - `parse_donning_doffing_armor_table()` - Simple 2-column
  - `parse_exchange_rates_table()` - 5-column currency grid
  - `parse_mounts_and_other_animals_table()` - 4-column layout
  - `parse_adventure_gear_table()` - 4 categories with metadata
  - `parse_tools_table()` - 3 categories with metadata
  - `parse_tack_harness_vehicles_table()` - Saddle subcategories (special logic)
  - `parse_armor_table()` - Multi-column (AC, Strength, Stealth)
  - `parse_weapons_table()` - Multi-column + categories
- Estimated reduction: ~300-400 more lines
- Target: <900 lines total (from 1386 baseline)

**Quality Metrics:**
- ✅ 5/14 parsers refactored (35% complete)
- ✅ Zero behavioral change (all 37 tables extract identically)
- ✅ File reduced 9.5% (1386 → 1255 lines)
- ✅ All tests passing

**Benefits:**
- Reduced code duplication
- Consistent extraction patterns
- Easier to maintain and extend
- Foundation for future config-driven architecture

**Next Steps:**
- User decision: Continue Phase 3 or pause refactor
- Option A: Refactor remaining 8 parsers (~2-3 hours work)
- Option B: Defer to future, focus on v0.10.0 Conditions

---

## **v0.10.0 — Conditions Dataset** **[FEATURE]** 📋 PLANNED

**Status:** PLANNED - Next priority feature
**Priority:** HIGH - Frequently referenced
**Effort:** Medium (~15-20 conditions)
**Consumer Impact:** NEW - Status conditions dataset

**Goal:** Extract ~15-20 status conditions from SRD 5.1.

**Why Conditions?**
- Referenced constantly (poisoned, stunned, charmed, frightened, etc.)
- Needed for monster abilities and spell effects
- Small dataset = quick confidence builder
- Unlocks better monster/spell integration

**Implementation:**
- `src/srd_builder/extract_conditions.py` - PDF extraction
- `src/srd_builder/parse_conditions.py` - Pure parsing
- `schemas/condition.schema.json` - Schema definition
- Add to build.py pipeline

**Conditions to Extract:**
- Blinded, Charmed, Deafened, Frightened, Grappled
- Incapacitated, Invisible, Paralyzed, Petrified, Poisoned
- Prone, Restrained, Stunned, Unconscious, Exhaustion (levels 1-6)
   - Travel expenses
   - Downtime activities

**Why Separate Tables?**
- Equipment items in equipment.json: Detailed integration data
- Equipment tables in tables.json: Quick reference for comparison
- Both needed for different use cases

**Impact on Future Work:**
- Better table extraction = easier conditions extraction (v0.10.0)
- Improved header detection = better feature parsing (v0.11.0)
- Infrastructure investment pays dividends immediately

**Implementation:**
- `src/srd_builder/extract_tables.py` - Expand table detection and parsing
- Handle multi-page tables
- Preserve table formatting (headers, structure)
- Improve column alignment algorithms

**Testing:**
- Verify armor table has all 6 types
- Verify weapons table has all 18 weapons
- Verify class progression tables match classes.json data
- Test multi-page table handling

**Schema:** 1.4.0 (minor - table structure improvements)

---

## **v0.10.0 — Conditions Dataset** (Quick Win) **[DATA]**

**Status:** PLANNED - New dataset
**Priority:** MEDIUM
**Effort:** Low (small dataset, benefits from v0.9.0 table improvements)
**Consumer Impact:** NEW - ~15-20 status conditions

**Priority:** MEDIUM
**Effort:** Medium (derived from classes/lineages)
**Consumer Impact:** NEW - Standalone searchable features

**Goal:** Extract class features and racial traits as standalone, searchable entities.

**Why Features?**
- Enables feature search without parsing class tables ("find all features that grant advantage")
- Clean API for character builders
- Reference for multiclassing feature interactions
- Originally scoped in Week 5 of initial plan
- Benefits from v0.9.0 table extraction improvements (class progression tables)

**Scope:**
- Class features (Action Surge, Spellcasting, Rage, etc.)
- Racial traits (Darkvision, Stonecunning, Lucky, etc.)
- Feature progressions (scales with level)
- Cross-references to parent class/lineage

**Schema:**
```json
{
  "id": "feature:action_surge",
  "simple_name": "action_surge",
  "name": "Action Surge",
  "summary": "Take an additional action on your turn",
  "source": "class:fighter",
  "level_acquired": 2,
  "text": "...",
  "mechanics": {
    "recharge": "short_rest"
  }
}
```

---

## **v0.11.0 — Features Dataset** **[DATA]**

**Status:** PLANNED - New dataset
**Priority:** MEDIUM
**Effort:** Medium (derived from classes/lineages)
**Consumer Impact:** NEW - Standalone searchable features

**Goal:** Extract class features and racial traits as standalone, searchable entities.

**Why Features?**
- Enables feature search without parsing class tables ("find all features that grant advantage")
- Clean API for character builders
- Reference for multiclassing feature interactions
- Originally scoped in Week 5 of initial plan
- Benefits from v0.9.0 table extraction improvements (class progression tables)

**Scope:**
- Class features (Action Surge, Spellcasting, Rage, etc.)
- Racial traits (Darkvision, Stonecunning, Lucky, etc.)
- Feature progressions (scales with level)
- Cross-references to parent class/lineage

**Schema:**
```json
{
  "id": "feature:action_surge",
  "simple_name": "action_surge",
  "name": "Action Surge",
  "summary": "Take an additional action on your turn",
  "source": "class:fighter",
  "level_acquired": 2,
  "text": "...",
  "mechanics": {
    "recharge": "short_rest"
  }
}
```

---

## **v0.12.0 — Rules Dataset** **[DATA]**

**Priority:** MEDIUM
**Effort:** High (complex text parsing)
**Consumer Impact:** NEW - Core mechanics and variant rules

**Goal:** Extract core mechanics, variant rules, and optional rules from SRD 5.1.

**Why Rules?**
- Combat rules (attack, damage, cover)
- Spellcasting rules (concentration, components)
- Conditions mechanics (detailed effects)
- Variant rules (feats, multiclassing)
- Originally scoped in Week 6 of initial plan

**Challenges:**
- Most complex text parsing (not tables or stat blocks)
- Least structured data in SRD
- Requires careful rule text segmentation

**Scope:**
- Core mechanics (ability checks, saving throws, combat)
- Spellcasting rules
- Movement and exploration
- Variant rules (feats, multiclassing prerequisites)
- Optional rules

---

## **v0.13.0 — Quality & Polish** **[QUALITY]**

**Priority:** HIGH - Required before v1.0.0
**Effort:** Medium
**Consumer Impact:** IMPROVED - Better data quality across all datasets

**Goal:** Final quality pass before v1.0.0 - address remaining data quality issues and technical debt.

**Why Before v1.0.0?**
- Clean up known technical debt
- Improve data quality metrics
- Polish rough edges identified during v0.8.x-v0.9.x development
- Ensure production-ready state for all datasets

**Scope:**

### Equipment Polish
1. **Properties Normalization** (MEDIUM)
   - Clean embedded data: `"versatile (1d10)"` → `"versatile"`
   - Data already in structured fields (versatile_damage, range)
   - Impact: Cleaner rule automation

2. **Container Capacity** (HIGH - Technical Debt)
   - Currently: 8/13 containers from PDF + 5/13 hardcoded
   - Root cause: Multi-column table extraction issues
   - Fix: Improve multi-column table handling, remove hardcoded values
   - See: PARKING_LOT.md for details

3. **Weapon Subcategory Normalization** (LOW)
   - "Martial Melee" → "martial_melee" (consistent with simple_name style)
   - Update DATA_DICTIONARY.md with normalized values

### Monster Polish
1. **Action Parsing Coverage** (MEDIUM)
   - Current: 472/884 actions (53.4%) with structured fields
   - Remaining: 412 non-attack actions (Multiattack, utility, buffs)
   - Opportunity: Parse ability checks, condition infliction patterns
   - Note: Many already have saving_throw field for debuffs

2. **Legendary Action Cost** (LOW)
   - Extract "(Costs 2 Actions)" from action names
   - Add action_cost field (default 1)
   - Clean names: "Paralyzing Touch (Costs 2 Actions)" → "Paralyzing Touch"

### Cross-Dataset Validation
1. **ID Resolution** (MEDIUM)
   - Validate references across datasets (class features → spells, monster spellcasting → spells)
   - Flag broken references
   - Build dependency graph

2. **Data Quality Metrics** (LOW)
   - Document coverage percentages for all effect fields
   - Create quality dashboard/report
   - Track improvements over time

**Out of Scope:**
- Spellcasting trait structure (requires Features dataset v0.10.0)
- Equipment references in monster actions (requires fuzzy matching)
- Subrace trait inheritance (current duplication approach is pragmatic)
- Feature references and multiclassing (depends on Features/Rules datasets)

**Success Criteria:**
- [ ] Equipment properties cleaned (no embedded data)
- [ ] Container capacity 13/13 from PDF (no hardcoded values)
- [ ] Monster action coverage >60% (add ~50 utility actions)
- [ ] Cross-dataset references validated
- [ ] All technical debt items from TODO.md addressed or moved to PARKING_LOT
- [ ] Ready for v1.0.0 stable release

---

## **v1.0.0 — Complete SRD 5.1 in JSON** 🚀

**Goal:** First stable release with complete SRD 5.1 coverage and production-ready quality.

**Prerequisites:**
- All datasets complete (v0.10.0 Conditions, v0.11.0 Features, v0.12.0 Rules)
- v0.13.0 Quality & Polish complete

**Complete SRD 5.1 Coverage (11 datasets):
- ✅ Monsters (296)
- ✅ Equipment (106)
- ✅ Spells (319)
- ✅ Reference Tables (~15)
- ✅ Classes (~13)
- ✅ Lineages (~9)
- ✅ Conditions (~15)
- ✅ Features (~150-200)
- ✅ Rules (core mechanics)

**Why This is v1.0.0:**
- Complete extraction of SRD 5.1 content
- Cannot move to SRD 5.2.1 until 5.1 is complete
- First stable release with full dataset
- Ready for consumer integration

**First GitHub Release:**
- Complete dataset bundle (all 9 JSON files)
- Full changelog (v0.1.0 → v1.0.0)
- Consumer documentation
- Example code
- License attribution

**Post-1.0.0:**
- v1.x.x - Bug fixes, data quality improvements for SRD 5.1
- v2.0.0 - SRD 5.2.1 extraction (new ruleset)

---

### Principles

* **Source of truth:** the PDF, not pre-existing JSON.
* **Fixtures:** used only for unit/golden tests.
* **Determinism:** identical inputs yield identical outputs.
* **Layered:** extract → parse → postprocess → index → validate.
* **No timestamps in dataset files.**

---
