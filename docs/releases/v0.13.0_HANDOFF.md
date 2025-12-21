# 🎯 Handoff Document: v0.13.0 - Creature System Overhaul

**Date:** November 9, 2025
**Version:** v0.13.0 (Grand Slam: v0.12.0 + v0.13.0 combined)
**Handed off to:** Blackmoor
**Prepared by:** Wolftales + GitHub Copilot

---

## Executive Summary

**What Changed:**
- Extended creature extraction from pages 261-394 → **261-403** (added 21 creatures)
- Discovered and extracted 95 miscellaneous creatures from Appendix MM-A (pages 366-394) that were already in range
- Implemented **three-tier ID system** for semantic separation: `monster:`, `creature:`, `npc:`
- Total creatures increased from **296 → 317** (201 monsters + 95 creatures + 21 NPCs)
- All three types remain in single `monsters.json` file but indexed separately

**Impact:**
- ✅ v0.12.0 (NPCs) - COMPLETE
- ✅ v0.13.0 (Misc Creatures) - COMPLETE
- Both milestones delivered simultaneously ("grand slam")
- 87% of SRD 5.1 dataset coverage complete (13/15 datasets)

---

## 1. Data Architecture Changes

### Three-Tier ID System

**Before (v0.11.0):**
```json
{
  "id": "monster:aboleth",
  "name": "Aboleth",
  "page": 261
}
```

**After (v0.13.0):**
```json
// Main bestiary (pages 261-365)
{
  "id": "monster:aboleth",
  "name": "Aboleth",
  "page": 261
}

// Appendix MM-A (pages 366-394)
{
  "id": "creature:awakened_shrub",
  "name": "Awakened Shrub",
  "page": 381
}

// Appendix MM-B (pages 395-403)
{
  "id": "npc:acolyte",
  "name": "Acolyte",
  "page": 395
}
```

**Rationale:**
- Semantic separation while maintaining accessibility in single file
- Page-based prefix assignment (automatic during parsing)
- Enables separate indexing and filtering by creature category
- Users can distinguish NPCs/summoned creatures from main monsters

### Page Range Extension

**Extraction boundaries changed:**

| Component | Old Range | New Range | Change |
|-----------|-----------|-----------|--------|
| Monsters (main) | 261-365 | 261-365 | No change |
| Creatures (MM-A) | ❌ Not extracted | 366-394 | ✅ **NEW** |
| NPCs (MM-B) | ❌ Not extracted | 395-403 | ✅ **NEW** |
| **Total pages** | 261-394 | 261-403 | +9 pages |

**File modified:** `src/srd_builder/extract_monsters.py` (line 35)
```python
# OLD
page_end: int = 394  # End of Monster Manual

# NEW
page_end: int = 403  # Include "Appendix MM-B: Nonplayer Characters" (395-403)
```

---

## 2. Code Changes by Module

### A. Parser (`src/srd_builder/parse_monsters.py`)

**Function:** `normalize_monster()` (lines 372-381)

**What Changed:**
Added page-based ID prefix determination:

```python
# Determine ID prefix based on page number
if 395 <= page <= 403:
    # Appendix MM-B: Nonplayer Characters (pages 395-403)
    id_prefix = "npc"
elif 366 <= page <= 394:
    # Appendix MM-A: Miscellaneous Creatures (pages 366-394)
    id_prefix = "creature"
else:
    # Main Monster Manual section (pages 261-365)
    id_prefix = "monster"

patched["id"] = f"{id_prefix}:{simple_name}"
```

**Impact:**
- Parser automatically assigns correct prefix during extraction
- No manual categorization needed
- Deterministic: page number → prefix mapping

---

### B. Postprocessor (`src/srd_builder/postprocess/`)

**Function:** `unify_simple_name()` (lines 59-67)

**What Changed:**
Preserve existing ID prefix instead of forcing "monster:":

```python
# OLD (forced all IDs to monster:)
patched["id"] = f"monster:{simple_name}"

# NEW (preserves existing prefix)
existing_id = m.get("id")
if existing_id and ":" in existing_id:
    prefix = existing_id.split(":")[0]
    patched["id"] = f"{prefix}:{simple_name}"
else:
    patched["id"] = f"monster:{simple_name}"
```

**Why Critical:**
- Without this fix, postprocessing was overwriting `creature:` and `npc:` back to `monster:`
- Caused test failures and broke semantic separation
- Now respects ID prefixes assigned during parsing

---

### C. Indexer (`src/srd_builder/indexer.py`)

**Function:** `build_indexes()` (lines 495-523)

**What Changed:**
Split creature list into three categories and build separate indexes:

```python
# Split monsters into three categories by ID prefix
actual_monsters = [m for m in monsters if m["id"].startswith("monster:")]
misc_creatures = [m for m in monsters if m["id"].startswith("creature:")]
npcs = [m for m in monsters if m["id"].startswith("npc:")]

# Build separate indexes for each category
indexes["monsters"] = _build_monster_indexes(actual_monsters)
indexes["creatures"] = _build_monster_indexes(misc_creatures)
indexes["npcs"] = _build_monster_indexes(npcs)
```

**New Entity Indexes:**
- Added `_build_creature_entity_index()` for creatures
- Added `_build_npc_entity_index()` for NPCs
- All three types appear in `index.entities` with correct type metadata

**Index Structure (index.json):**
```json
{
  "monsters": {
    "by_name": {"aboleth": "monster:aboleth", ...},
    "by_cr": {"5": ["monster:air_elemental", ...]},
    "by_type": {"dragon": [...]},
    "by_size": {"Large": [...]}
  },
  "creatures": {
    "by_name": {"awakened_shrub": "creature:awakened_shrub", ...},
    "by_cr": {"0": ["creature:awakened_shrub", ...]},
    "by_type": {"plant": [...]},
    "by_size": {"Small": [...]}
  },
  "npcs": {
    "by_name": {"acolyte": "npc:acolyte", ...},
    "by_cr": {"0.25": ["npc:acolyte", ...]},
    "by_type": {"humanoid": [...]},
    "by_size": {"Medium": [...]}
  },
  "entities": {
    "monsters": {"monster:aboleth": {"type": "monster", "file": "monsters.json"}},
    "creatures": {"creature:awakened_shrub": {"type": "creature", "file": "monsters.json"}},
    "npcs": {"npc:acolyte": {"type": "npc", "file": "monsters.json"}}
  },
  "stats": {
    "total_monsters": 201,
    "total_creatures": 95,
    "total_npcs": 21
  }
}
```

---

## 3. Test Updates

### Count Expectations

**Updated files:**
- `tests/test_dataset_completeness.py` (line 18): 296 → 317
- `tests/test_extract_basic.py`: Updated counts and page range (261-394 → 261-403)
- `tests/test_extract_cross_page.py`: Updated count expectation
- `tests/test_golden_monsters.py`: Regenerated fixtures with new `creature:` IDs

**Fixed:**
- `tests/test_indexer_conflicts.py`: Added proper "monster:" prefix to test data

**Status:** All 161 tests passing ✅

### Fixture Regeneration

**Modified fixture:** `tests/fixtures/srd_5_1/normalized/monsters.json`
- Now includes creatures with `creature:` prefix (e.g., `creature:awakened_shrub`)
- Deterministic output verified via golden test
- Schema v1.3.0 metadata updated

---

## 4. Documentation Updates

### Updated Files

| File | Changes |
|------|---------|
| `docs/ROADMAP.md` | Marked v0.12.0 and v0.13.0 complete; updated monster count to 317 |
| `docs/BUNDLE_README.md` | Updated version to v0.13.0; documented three-tier system; updated index structure examples |
| `docs/DATA_DICTIONARY.md` | Documented `monster:`/`creature:`/`npc:` prefix system; updated ID field documentation; added version history entry |

### Key Documentation Sections Added

**BUNDLE_README.md:**
- Three-tier index structure with examples
- Entity directory showing all three types
- Updated stats (201 monsters, 95 creatures, 21 NPCs)

**DATA_DICTIONARY.md:**
- Page-based prefix determination rules (366-394 = creature, 395-403 = npc, else monster)
- Semantic separation rationale
- Updated namespace prefix documentation

---

## 5. Dataset Statistics

### Before v0.13.0 (v0.11.0)

```
Creatures: 296 (all classified as "monster:")
Pages extracted: 261-394
```

### After v0.13.0

```
Total creatures: 317
├── Monsters (monster:)    201 creatures (pages 261-365)
├── Creatures (creature:)   95 creatures (pages 366-394, Appendix MM-A)
└── NPCs (npc:)             21 creatures (pages 395-403, Appendix MM-B)

Pages extracted: 261-403 (+9 pages)
File: monsters.json (single file, semantically separated)
Indexes: 3 separate indexes (monsters, creatures, npcs)
```

### Example Creatures by Type

**Monsters (201):** Aboleth, Adult Red Dragon, Air Elemental, Beholder, Tarrasque, etc.

**Creatures (95):** Awakened Shrub, Awakened Tree, Animated Armor, Flying Sword, Homunculus, Shadow Demon, etc.

**NPCs (21):** Acolyte, Archmage, Assassin, Bandit Captain, Gladiator, Knight, Mage, Priest, Veteran, etc.

---

## 6. Breaking Changes

### ⚠️ Potential Consumer Impact

**API consumers using `index.monsters`:**

**Before:**
```javascript
// All 296 creatures were in index.monsters
const allCreatures = index.monsters.by_name;
console.log(Object.keys(allCreatures).length);  // 296
```

**After:**
```javascript
// Now split into three indexes
const monsters = index.monsters.by_name;    // 201
const creatures = index.creatures.by_name;  // 95
const npcs = index.npcs.by_name;            // 21

// To get ALL creatures (if needed)
const allCreatures = {
  ...index.monsters.by_name,
  ...index.creatures.by_name,
  ...index.npcs.by_name
};
console.log(Object.keys(allCreatures).length);  // 317
```

**Migration Path:**
- If consumers need "all creatures regardless of type": merge three indexes
- If consumers need semantic filtering: use separate indexes (e.g., only NPCs for character encounters)
- `monsters.json` file still contains all 317 - only indexing changed

---

## 7. Quality Assurance

### Test Coverage
- ✅ All 161 tests passing
- ✅ Golden fixtures regenerated and validated
- ✅ Count expectations updated across all test files
- ✅ Indexer conflict tests fixed

### Linting & Formatting
- ✅ `ruff check .` - clean
- ✅ `black --check .` - clean
- ⚠️ Pre-existing mypy warning (unrelated to this change)

### Manual Validation
- ✅ Verified creature extraction completeness (pages 366-403)
- ✅ Confirmed ID prefixes match page ranges
- ✅ Validated index separation (by_cr, by_type, by_size all work correctly)
- ✅ Entity directory includes all three types

---

## 8. Next Steps (v0.14.0+)

### Immediate Priorities

**v0.14.0 - Magic Items:**
- Extract magic weapons, armor, wondrous items
- Implement `variant_of` field (e.g., +1 Longsword → longsword)
- Add `is_magic`, `rarity`, `requires_attunement` fields
- Schema already prepared in equipment.schema.json

**v0.15.0 - Rules Dataset:**
- Extract core mechanics (advantage, saving throws, combat actions)
- Move CALCULATED tables to rules dataset (ability scores, proficiency bonus)
- Complete SRD 5.1 extraction

**v1.0.0 - Stable Release:**
- All 15 datasets complete
- Final quality polish
- Production-ready deterministic builds

### Maintenance Notes

**If adding new creature categories in future:**
1. Add page range check in `parse_monsters.py` (normalize_monster function)
2. Update `postprocess/` if prefix preservation needs changes
3. Add index building in `indexer.py` (split list + build indexes)
4. Add entity index builder function
5. Update documentation (BUNDLE_README, DATA_DICTIONARY)
6. Update test expectations (counts, fixtures)

---

## 9. Files Modified Summary

### Core Implementation
```
src/srd_builder/extract_monsters.py    (line 35: page_end 394→403)
src/srd_builder/parse_monsters.py      (lines 372-381: ID prefix logic)
src/srd_builder/postprocess/         (lines 59-67: preserve prefixes)
src/srd_builder/indexer.py             (lines 495-523: split indexing)
                                       (lines 120-138: entity indexes)
```

### Tests
```
tests/test_dataset_completeness.py     (line 18: count 296→317)
tests/test_extract_basic.py            (counts and page range)
tests/test_extract_cross_page.py       (count expectation)
tests/test_golden_monsters.py          (fixture regeneration)
tests/test_indexer_conflicts.py        (ID prefix fix)
```

### Documentation
```
docs/ROADMAP.md                        (v0.12.0/v0.13.0 complete)
docs/BUNDLE_README.md                  (three-tier system docs)
docs/DATA_DICTIONARY.md                (prefix documentation)
```

### Fixtures
```
tests/fixtures/srd_5_1/normalized/monsters.json  (317 creatures with prefixes)
```

---

## 10. Key Insights & Decisions

### Why Single File with Semantic IDs?

**Rejected:** Creating separate `creatures.json` and `npcs.json` files

**Chosen:** Single `monsters.json` with three-tier ID prefixes

**Rationale:**
- Maintains backwards compatibility (file name unchanged)
- All creatures share identical schema (no structural differences)
- Semantic separation via ID prefix is lightweight and extensible
- Indexing provides separate access when needed
- Easier for consumers: one file to load, filter by ID prefix if needed

### Why Page-Based Prefix Assignment?

**Alternative considered:** Manual categorization or metadata-based rules

**Chosen:** Automatic page-range mapping in parser

**Benefits:**
- Deterministic: same page → same prefix always
- No manual intervention needed
- SRD structure naturally divides content by page range
- Future-proof: adding new sections just requires updating page ranges

### Why Separate Indexes?

**Alternative considered:** Combined index with `type` field on each entry

**Chosen:** Three top-level indexes (monsters, creatures, npcs)

**Benefits:**
- Cleaner API: `index.npcs.by_cr` vs `index.monsters.by_cr.filter(...)`
- Better discoverability (consumers see three categories immediately)
- Performance: no need to filter large lists
- Matches semantic separation of ID system

---

## 11. Lessons Learned

### What Went Well
- ✅ Opportunistic discovery: Found MM-A creatures during MM-B implementation
- ✅ ID prefix system scales elegantly (easy to add 4th category if needed)
- ✅ Postprocessor fix caught early via tests
- ✅ Documentation updated comprehensively before handoff

### What Could Improve
- Initially missed postprocessor was overwriting prefixes (caught by tests)
- Could have validated MM-A content earlier (was in range since v0.3.0)
- Future: Add explicit page range validation in tests

### Technical Debt
- None introduced - all changes follow existing patterns
- Preserved backwards compatibility where possible
- Documentation up to date

---

## 12. Contact & Support

**Questions?**
- Review this handoff document
- Check `docs/ROADMAP.md` for context
- See `docs/AGENTS.md` for workflow guidelines
- Run `pytest -q` to validate any changes

**Key Files to Review:**
1. This handoff doc (you are here)
2. `docs/BUNDLE_README.md` - Consumer-facing API changes
3. `docs/DATA_DICTIONARY.md` - Field documentation
4. `src/srd_builder/indexer.py` - Indexing logic
5. `src/srd_builder/parse_monsters.py` - ID prefix assignment

---

## Appendix: Quick Reference

### Creature Counts by Type
| Type | Prefix | Count | Pages | Examples |
|------|--------|-------|-------|----------|
| Monsters | `monster:` | 201 | 261-365 | Aboleth, Beholder, Dragon |
| Creatures | `creature:` | 95 | 366-394 | Awakened Shrub, Animated Armor |
| NPCs | `npc:` | 21 | 395-403 | Acolyte, Mage, Knight |
| **Total** | - | **317** | 261-403 | - |

### Command Reference
```bash
# Run full test suite
pytest -q

# Lint and format check
ruff check .
black --check .

# Rebuild dataset
python -m srd_builder.build

# Validate schema
jsonschema -i dist/srd_5_1/monsters.json schemas/monster.schema.json

# Check indexes
jq '.stats' dist/srd_5_1/index.json
```

### Version Info
- **Build Version:** v0.13.0
- **Schema Version:** v1.3.0
- **Test Status:** 161/161 passing ✅
- **Linting:** Clean ✅
- **Ready for:** Version bump, commit, tag, push

---

**End of Handoff Document**

*Prepared with ❤️ by Wolftales + GitHub Copilot*
*November 9, 2025*
