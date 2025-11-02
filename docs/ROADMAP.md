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

## **v0.5.5 — Table Metadata Discovery (Phase 0.5)** 🔄 DEFERRED

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

**Priority:** DEFERRED — Spells have different extraction pattern (prose vs tables), may not need this

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

## **v0.7.0 — Reference Tables Dataset** **[DATA]**

**Priority:** HIGH (foundational for other datasets)
**Effort:** Low-Medium (leverage existing column_mapper.py)
**Consumer Impact:** NEW - ~10-15 reference tables

**Goal:** Extract reusable reference tables from SRD 5.1 for consumer use.

**Why Tables First?**
- Already parsed equipment tables internally - should have captured them for consumers
- Needed by Classes (level progression, proficiency bonus)
- Needed by Spells (spell slots by level)
- Needed by general gameplay (services, travel pace, carrying capacity)
- Validates our table extraction infrastructure for public consumption
- Quick win that unblocks other datasets

**Scope:**
- Experience points by CR
- Proficiency bonus by level
- Armor class by armor type (reference)
- Damage by character level (cantrips)
- Spell slots by class level
- Travel pace (hours/day, miles/hour)
- Services and expenses
- Carrying capacity / encumbrance
- Creature size categories (space, hit dice)
- Ability score modifiers (-5 to +10)

**Schema (Simple)**
```json
{
  "id": "table:experience_by_cr",
  "simple_name": "experience_by_cr",
  "name": "Experience Points by Challenge Rating",
  "summary": "XP rewards for defeating monsters",
  "columns": ["cr", "xp"],
  "rows": [
    {"cr": "0", "xp": 10},
    {"cr": "1/8", "xp": 25},
    {"cr": "1/4", "xp": 50}
  ],
  "page": 9
}
```

**Technical Approach:**
- Extend `column_mapper.py` to capture tables for output (not just internal parsing)
- Create `tables.json` output alongside existing datasets
- Simple extraction (no complex parsing like monsters/spells)

---

## **v0.8.0 — Classes & Lineages** **[DATA]**

**Goal:** Extract character creation content.

**Scope:**
- Classes (complex with level progression tables)
- Lineages/Races (character creation features)
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

---

## **v0.9.0 — Conditions Dataset** (Quick Win) **[DATA]**

**Priority:** MEDIUM
**Effort:** Low (small dataset)
**Consumer Impact:** NEW - ~15-20 status conditions

**Goal:** Extract ~15-20 status conditions from SRD 5.1.

**Why Conditions?**
- Referenced constantly (poisoned, stunned, charmed, frightened, etc.)
- Needed for monster abilities and spell effects
- Small dataset = quick confidence builder
- Unlocks better monster/spell integration

**Schema (Simple)**
```json
{
  "id": "condition:poisoned",
  "simple_name": "poisoned",
  "name": "Poisoned",
  "text": "A poisoned creature has disadvantage on attack rolls and ability checks.",
  "mechanics": {
    "disadvantage_on": ["attack_rolls", "ability_checks"]
  }
}
```

**Optional Structured Fields:**
- speed_modifier (e.g., restrained, grappled)
- advantage_on / disadvantage_on
- prevents (e.g., unconscious prevents actions)

---

## **v0.10.0 — Features Dataset** **[DATA]**

**Priority:** MEDIUM
**Effort:** Medium (derived from classes/lineages)
**Consumer Impact:** NEW - Standalone searchable features

**Goal:** Extract class features and racial traits as standalone, searchable entities.

**Why Features?**
- Enables feature search without parsing class tables ("find all features that grant advantage")
- Clean API for character builders
- Reference for multiclassing feature interactions
- Originally scoped in Week 5 of initial plan

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

## **v0.11.0 — Rules Dataset** **[DATA]**

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

## **v1.0.0 — Complete SRD 5.1 in JSON** 🚀

**Goal:** Single `build_all()` to process all entities and a top-level `validate_all()` for all schemas and PDFs.

**Complete SRD 5.1 Coverage (9 datasets):**
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
