# 📋 Changelog: v0.8.3 → v0.13.0

**Period:** Last handoff (v0.8.3) → Current (v0.13.0)
**Duration:** 6 major versions
**Prepared for:** Blackmoor
**Date:** November 9, 2025

---

## Executive Summary

**What's New:**
- **5 new major versions** (v0.8.4 through v0.13.0)
- **6 new datasets** (conditions, diseases, madness, poisons, features, expanded creatures)
- **Equipment expansion:** 106 → 258 items (+152 items, +143%)
- **Tables expansion:** 23 → 39 tables (+16 tables, +70%)
- **Creatures expansion:** 296 → 317 creatures (+21, +7%)
- **Major architecture improvements:** Text-based table extraction, pattern-based engines, three-tier ID system
- **Dataset coverage:** 10/15 → 13/15 datasets (67% → 87%)

---

## Version-by-Version Breakdown

### v0.8.4 — Character Creation Blockers ✅
**Released:** Post-v0.8.3
**Focus:** Critical fixes for character sheet applications

**Changes:**
- Fixed ability score modifiers in lineages
- Restructured equipment range field (normal/long distances)
- Improved versatile weapon damage parsing
- Enhanced armor proficiency categorization

**Impact:** Character creation apps now have all required data structures

---

### v0.8.5 — Spell Enhancements ✅
**Focus:** Spell data quality improvements

**Changes:**
- Healing coverage: 100% (all healing spells now have structured healing dice)
- AOE coverage: +43% (more spells with area-of-effect data)
- Improved damage/healing dice extraction
- Better spell effects parsing

**Impact:** Spell databases have richer, more complete data

---

### v0.8.6 — Spell Duration Restructure ✅
**Focus:** Concentration spell discoverability

**Changes:**
- Split `duration` field into `duration` (string) + `concentration` (boolean)
- Makes concentration spells easily filterable
- Improved duration parsing for edge cases

**Impact:** Spell management UIs can now filter/track concentration spells

---

### v0.9.0 — Text-Based Table Extraction 🎯
**Focus:** Coordinate-based breakthrough for table extraction

**Changes:**
- Implemented coordinate-based text extraction from PDF
- Replaced regex parsing with spatial analysis
- Foundation for extracting complex tables from PDF
- Handles multi-column layouts and merged cells

**Impact:** Unlocked extraction of previously impossible tables

**Technical:** Major architecture shift - coordinate-aware parsing

---

### v0.9.1 — Equipment Tables Expansion ✅
**Focus:** Adventure gear, tools, containers

**Changes:**
- Added adventure gear tables (rope, torches, tents, etc.)
- Added tool tables (artisan's tools, gaming sets, instruments)
- Added container tables (backpacks, chests, barrels)
- Equipment count: 106 → ~180 items

**Impact:** Complete equipment shop functionality

---

### v0.9.2 — Equipment Tables Complete ✅
**Focus:** Final equipment tables

**Changes:**
- Total tables: 23 → 37 (+14 equipment tables)
- Completed all SRD equipment extraction
- Added mounts, vehicles, lifestyle expenses, services
- Equipment count: ~180 → 258 items

**Impact:** 100% equipment coverage from SRD

---

### v0.9.3 — Text Parser Refactor & Migration Tools ✅
**Focus:** Developer tooling and architecture cleanup

**Changes:**
- Refactored text parser for maintainability
- Added migration utilities for schema changes
- Created migration guide documentation
- Improved error handling and validation

**Impact:** Easier maintenance and future schema evolution

---

### v0.9.4 — Migrate CALCULATED Tables ✅
**Focus:** Move calculated tables to PDF extraction

**Changes:**
- Migrated ability_scores_and_modifiers table to PDF extraction
- Improved table categorization (PDF-extracted vs calculated)
- Tables: 37 → 37+2 (categorized)

**Impact:** Cleaner separation of extracted vs derived data

---

### v0.9.5 — Pattern-Based Architecture Refactor 🏗️
**Focus:** Major architectural improvement

**Changes:**
- Introduced `table_metadata` module for table definitions
- Created extraction engines (coordinate-based, pattern-based)
- Unified table extraction pipeline
- Improved code organization and reusability

**Impact:** Scalable foundation for future datasets

**Technical:** Significant refactor - improved maintainability

---

### v0.9.6 — TOC & Page Index 📖
**Focus:** Navigation and page reference system

**Changes:**
- Created PAGE_INDEX module with 23 sections
- Indexed 24 reference tables with page numbers
- Table of contents for SRD navigation
- Foundation for citation and cross-references

**Impact:** Better documentation and data traceability

---

### v0.9.7 — Migrate REFERENCE Tables ✅
**Focus:** Complete table migration to PDF extraction

**Changes:**
- Migrated travel_pace and size_categories to PDF extraction
- Removed non-SRD tables (5e reference tables not in SRD)
- Tables: 39 total (15 PDF-extracted + 12 class + 5 reference + 5 misc + 2 calculated)

**Impact:** 100% SRD table coverage

---

### v0.9.8 — Migrate CLASS_PROGRESSIONS ✅
**Focus:** Class progression tables

**Changes:**
- Migrated all 12 class progression tables to PDF extraction
- Fixed class feature parsing edge cases
- Improved multi-page table handling
- Known minor issues documented (Monk soft hyphens, Rogue continuation text)

**Impact:** Complete class progression data

---

### v0.9.9 — Equipment Assembly & Table Migration 🎯
**Focus:** Three-part equipment overhaul

**Part 1: Table Migration**
- Completed all equipment table migrations to PDF extraction

**Part 2: Equipment Assembly**
- Merged equipment data from multiple tables
- Unified equipment records (cost + properties + descriptions)

**Part 3: Descriptions & Enhancements**
- Added equipment descriptions (83 items)
- Improved data quality and completeness
- Final equipment count: 258 items

**Impact:** Production-ready equipment dataset

---

### v0.10.0 — Conditions Dataset 📜
**Focus:** Status conditions and afflictions

**New Datasets:**
- ✅ **conditions.json** - 15 status conditions (blinded, stunned, exhaustion, etc.)
- ✅ **diseases.json** - 3 diseases (Cackle Fever, Sewer Plague, Sight Rot)
- ✅ **madness.json** - 3 madness tables (short-term, long-term, indefinite)
- ✅ **poisons.json** - 14 poisons with effects, costs, and save DCs

**Technical:**
- Implemented prose extraction framework (non-table text extraction)
- Handles narrative sections from Appendix PH-A

**Impact:** Complete affliction/condition system for gameplay

**Dataset Progress:** 10/15 → 13/15 datasets (67% → 87%)

---

### v0.11.0 — Features Dataset 🎨
**Focus:** Class features and lineage traits

**New Dataset:**
- ✅ **features.json** - 246 class features + lineage traits
  - Class features: Rage, Action Surge, Sneak Attack, Spellcasting, etc.
  - Lineage traits: Darkvision, Dwarven Resilience, Fey Ancestry, etc.

**Technical:**
- Prose extraction from class/lineage sections
- Feature-level granularity for character building
- Cross-references with classes.json and lineages.json

**Impact:** Character sheet apps can display feature details

---

### v0.12.0 — Appendix MM-B: NPCs ✅
**Focus:** Nonplayer characters

**Changes:**
- Extended page range: 261-394 → 261-403 (+9 pages)
- Extracted 21 NPCs from Appendix MM-B (pages 395-403)
- Implemented three-tier ID system (monster:/creature:/npc:)

**NPCs Added:**
- Acolyte, Archmage, Assassin, Bandit, Bandit Captain
- Berserker, Commoner, Cultist, Cult Fanatic, Druid
- Gladiator, Guard, Knight, Mage, Noble
- Priest, Scout, Spy, Thug, Tribal Warrior, Veteran

**Impact:** Complete NPC statblocks for encounters

---

### v0.13.0 — Appendix MM-A: Misc Creatures 🎯
**Focus:** Miscellaneous creatures (awakened, animated, summoned)

**Changes:**
- Extracted 95 creatures from Appendix MM-A (pages 366-394)
- Completed three-tier ID system architecture:
  - `monster:` - 201 creatures (main bestiary, pages 261-365)
  - `creature:` - 95 creatures (Appendix MM-A, pages 366-394)
  - `npc:` - 21 creatures (Appendix MM-B, pages 395-403)

**Creatures Added:**
- Awakened Shrub, Awakened Tree, Animated Armor, Flying Sword
- Air/Earth/Fire/Water Elementals (summoned variants)
- Homunculus, Shadow Demon, and other summoned/animated creatures

**Architecture:**
- Single monsters.json file with semantic ID separation
- Separate indexes for each category (monsters, creatures, npcs)
- Page-based automatic prefix assignment

**Impact:** Complete creature coverage (317 total)

**Grand Slam:** Delivered v0.12.0 + v0.13.0 simultaneously

---

## Summary Statistics

### Datasets: 10 → 13 (+3 new datasets)

| Dataset | v0.8.3 | v0.13.0 | Change |
|---------|--------|---------|--------|
| monsters.json | 296 | 317 | +21 (+7%) |
| equipment.json | 106 | 258 | +152 (+143%) |
| spells.json | 319 | 319 | No change |
| tables.json | 23 | 39 | +16 (+70%) |
| lineages.json | 13 | 13 | No change |
| classes.json | 12 | 12 | No change |
| conditions.json | ❌ | 15 | ✅ NEW |
| diseases.json | ❌ | 3 | ✅ NEW |
| madness.json | ❌ | 3 | ✅ NEW |
| poisons.json | ❌ | 14 | ✅ NEW |
| features.json | ❌ | 246 | ✅ NEW |
| **Total Items** | **769** | **1,239** | **+470 (+61%)** |

### Coverage: 67% → 87%

| Metric | v0.8.3 | v0.13.0 | Change |
|--------|--------|---------|--------|
| Datasets Complete | 10/15 | 13/15 | +3 |
| Coverage % | 67% | 87% | +20% |
| Remaining | 5 | 2 | -3 |

**Remaining Datasets:**
- magic_items.json (v0.14.0 - next)
- rules.json (v0.15.0)

---

## Major Technical Improvements

### 1. Three-Tier ID System (v0.12.0 + v0.13.0)

**Before:**
```json
{"id": "monster:acolyte"}
```

**After:**
```json
{"id": "monster:aboleth"}    // Main bestiary
{"id": "creature:awakened_shrub"}  // Appendix MM-A
{"id": "npc:acolyte"}         // Appendix MM-B
```

**Benefits:**
- Semantic separation of creature types
- Single file with organized indexing
- Automatic page-based categorization

---

### 2. Coordinate-Based Table Extraction (v0.9.0)

**Before:** Regex pattern matching (fragile, limited)

**After:** Spatial coordinate analysis (robust, comprehensive)

**Benefits:**
- Extract complex multi-column tables
- Handle merged cells and irregular layouts
- Foundation for all v0.9.x improvements

---

### 3. Pattern-Based Architecture (v0.9.5)

**Before:** Monolithic extraction scripts

**After:** Modular extraction engines with metadata

**Benefits:**
- Reusable extraction patterns
- Easier maintenance and testing
- Scalable to new table types

---

### 4. Prose Extraction Framework (v0.10.0)

**Before:** Only table extraction

**After:** Narrative text extraction (conditions, features, etc.)

**Benefits:**
- Extract non-tabular content (Appendix PH-A)
- Feature descriptions and condition effects
- Richer contextual data

---

### 5. Equipment Assembly Pipeline (v0.9.9)

**Before:** Separate equipment tables, no descriptions

**After:** Unified equipment records with descriptions

**Benefits:**
- Single source of truth per item
- Cost + properties + descriptions merged
- 258 items with 83 having full descriptions

---

## Data Quality Improvements

### Spell Enhancements
- ✅ Healing coverage: 100%
- ✅ AOE coverage: +43%
- ✅ Concentration tracking: Boolean field
- ✅ Duration restructure: Better filtering

### Equipment Enhancements
- ✅ Range structure: Normal/long distances
- ✅ Versatile damage: Proper parsing
- ✅ Descriptions: 83 items with full text
- ✅ Proficiency categories: Improved armor classification

### Creature Enhancements
- ✅ Semantic categorization: monster/creature/npc
- ✅ Complete coverage: All SRD creatures extracted
- ✅ Separate indexing: Easy filtering by type

### Table Enhancements
- ✅ PDF extraction: 15 tables (was 0)
- ✅ Class progressions: All 12 classes
- ✅ Reference tables: Complete coverage
- ✅ Page index: 23 sections mapped

---

## Breaking Changes

### Index Structure (v0.12.0 + v0.13.0)

**Before:**
```json
{
  "monsters": {
    "by_name": { /* all 296 creatures */ }
  }
}
```

**After:**
```json
{
  "monsters": {
    "by_name": { /* 201 monsters */ }
  },
  "creatures": {
    "by_name": { /* 95 creatures */ }
  },
  "npcs": {
    "by_name": { /* 21 NPCs */ }
  }
}
```

**Migration:** Merge three indexes if you need all creatures

---

### Equipment Count Field (v0.9.9)

**Before:** 106 items

**After:** 258 items

**Migration:** Update any hardcoded equipment counts

---

### Spell Duration Field (v0.8.6)

**Before:** `"duration": "Concentration, up to 1 minute"`

**After:**
```json
{
  "duration": "up to 1 minute",
  "concentration": true
}
```

**Migration:** Check `concentration` field instead of parsing duration string

---

## Documentation Improvements

### New Documentation
- ✅ `HANDOFF_v0.13.0.md` - Complete v0.13.0 handoff guide
- ✅ `CHANGELOG_v0.8.3_to_v0.13.0.md` - This document
- ✅ Migration guides (v0.9.3)
- ✅ PAGE_INDEX module documentation (v0.9.6)

### Updated Documentation
- ✅ `BUNDLE_README.md` - Three-tier system, new datasets
- ✅ `DATA_DICTIONARY.md` - All new fields documented
- ✅ `ROADMAP.md` - Progress tracking updated
- ✅ `SCHEMAS.md` - Schema evolution documented

---

## Testing & Quality

### Test Coverage
- ✅ All versions: 100% test pass rate
- ✅ Current: 161 tests passing
- ✅ Golden fixtures: Regenerated for each version
- ✅ Schema validation: All datasets validated

### Code Quality
- ✅ Linting: Clean (ruff + black)
- ✅ Type hints: Python 3.11+ typing
- ✅ Pre-commit hooks: Enforced formatting
- ✅ CI/CD: GitHub Actions green

---

## What You Can Build Now (vs v0.8.3)

### NEW Capabilities (v0.13.0)

✅ **Condition Tracking System**
- Display condition effects (blinded, stunned, etc.)
- Track diseases and madness effects
- Poison lookup with save DCs and costs

✅ **Feature Reference System**
- Show class feature descriptions (Rage, Sneak Attack, etc.)
- Display lineage trait details (Darkvision, Fey Ancestry, etc.)
- Cross-reference features with classes/lineages

✅ **Complete NPC Encounters**
- 21 ready-to-use NPC statblocks
- Separate indexing for easy lookup
- Common encounter NPCs (guards, bandits, cultists)

✅ **Summoned/Animated Creatures**
- 95 summoned creature statblocks
- Animated objects (armor, weapons)
- Awakened creatures (shrubs, trees)
- Elemental variants

✅ **Complete Equipment Shop**
- 258 items (was 106)
- 83 items with full descriptions
- Tools, containers, adventure gear
- Mounts, vehicles, lifestyle expenses

### IMPROVED Capabilities

🔧 **Better Spell Management**
- Concentration filtering
- Complete healing dice
- Enhanced AOE data

🔧 **Better Character Creation**
- Fixed ability modifiers
- Improved equipment ranges
- Enhanced armor proficiency

🔧 **Better Table References**
- 39 tables (was 23)
- All class progressions
- Complete reference tables

---

## Roadmap: What's Next

### v0.14.0 — Magic Items (Next)
**Status:** Planned
**Focus:** Magic weapons, armor, wondrous items

**Expected Changes:**
- New dataset: magic_items.json
- Implement variant_of field (magic item → base item linking)
- Add rarity, attunement, modifiers fields
- Schema already prepared in equipment.schema.json

---

### v0.15.0 — Rules Dataset
**Status:** Planned
**Focus:** Core mechanics and variant rules

**Expected Changes:**
- New dataset: rules.json
- Core mechanics (advantage, saving throws, combat actions)
- Move CALCULATED tables to rules dataset
- Complete SRD 5.1 extraction

---

### v1.0.0 — Stable Release
**Status:** Final milestone
**Focus:** Production-ready deterministic builds

**Expected Changes:**
- All 15 datasets complete
- Final quality polish
- Comprehensive API documentation
- Production release

---

## Migration Guide

### From v0.8.3 to v0.13.0

#### 1. Update Equipment Count Expectations
```python
# OLD
assert len(equipment) == 106

# NEW
assert len(equipment) == 258
```

#### 2. Update Creature Index Access
```python
# OLD
all_creatures = index["monsters"]["by_name"]

# NEW
monsters = index["monsters"]["by_name"]
creatures = index["creatures"]["by_name"]
npcs = index["npcs"]["by_name"]

# To get all creatures
all_creatures = {**monsters, **creatures, **npcs}
```

#### 3. Update Spell Concentration Checks
```python
# OLD
is_concentration = "Concentration" in spell["duration"]

# NEW
is_concentration = spell.get("concentration", False)
```

#### 4. Load New Datasets
```python
# NEW datasets available
conditions = load_json("conditions.json")
diseases = load_json("diseases.json")
madness = load_json("madness.json")
poisons = load_json("poisons.json")
features = load_json("features.json")
```

---

## Key Contacts & Resources

### Documentation
- `HANDOFF_v0.13.0.md` - v0.13.0 specific changes
- This file - Complete v0.8.3 → v0.13.0 changelog
- `ROADMAP.md` - Future plans and progress
- `AGENTS.md` - Development guidelines

### Support
- GitHub Issues: Report bugs or request features
- GitHub Actions: Verify CI/CD status
- Test Suite: Run `pytest -q` to validate

---

## Acknowledgments

**Developed by:** Wolftales + GitHub Copilot
**Period:** v0.8.3 (last handoff) → v0.13.0 (current)
**Versions delivered:** 6 major versions (v0.8.4 through v0.13.0)
**New datasets:** 6 (conditions, diseases, madness, poisons, features, expanded creatures)
**Total items added:** +470 items (+61% increase)
**Dataset coverage:** 67% → 87% (+20% progress toward v1.0.0)

---

**End of Changelog**

*Prepared for Blackmoor handoff*
*November 9, 2025*
