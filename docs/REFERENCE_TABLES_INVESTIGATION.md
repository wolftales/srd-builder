# Reference Tables Investigation - v0.9.7

**Date:** November 5, 2025
**Investigator:** GitHub Copilot
**Objective:** Determine which REFERENCE tables exist in SRD 5.1 PDF vs convenience/custom tables

---

## Executive Summary

**Investigation of 4 REFERENCE tables:**
- ✅ **travel_pace** - FOUND on page 84 (extract)
- ✅ **creature_size** - FOUND on page 92 (extract)
- ❌ **cantrip_damage** - NOT FOUND (convenience table, recommend removal)
- ❌ **spell_slots_by_level** - NOT FOUND standalone (embedded in class tables)

**Recommendation:** Extract 2 tables from PDF, decommission 2 convenience tables

---

## Detailed Findings

### 1. travel_pace ✅ EXTRACT

**Status:** **FOUND in PDF**
**Location:** Page 84 (Movement section)
**Tables detected:** 2 tables (1 row x 5 cols each)
**Recommendation:** **EXTRACT using legacy_parser**

**SRD Content:**
```
Pace             | Distance/Minute | Distance/Hour | Distance/Day
Fast             | 400 feet        | 4 miles       | 30 miles
Normal           | 300 feet        | 3 miles       | 24 miles
Slow             | 200 feet        | 2 miles       | 18 miles
```

**Current reference data:** ✓ Matches PDF exactly

**Action:**
- Update `table_metadata.py`: Change `pattern_type` from "reference" to "legacy_parser"
- Add `pages: [84]` configuration
- Create parser function `parse_travel_pace_table()` in `text_table_parser.py`
- Validate extraction matches current reference data

---

### 2. creature_size ✅ EXTRACT

**Status:** **FOUND in PDF**
**Location:** Page 92 (Combat section, "Size Categories" subsection)
**Tables detected:** 3 separate tables (PyMuPDF splits into 1-row tables)
**Recommendation:** **EXTRACT using legacy_parser or text_region**

**SRD Content:**
```
Size       | Space
Tiny       | 2½ by 2½ ft.
Small      | 5 by 5 ft.
Medium     | 5 by 5 ft.
Large      | 10 by 10 ft.
Huge       | 15 by 15 ft.
Gargantuan | 20 by 20 ft. or larger
```

**Current reference data:** ✓ Matches PDF exactly (including "2½" with ½ character)

**Action:**
- Update `table_metadata.py`: Change `pattern_type` from "reference" to "legacy_parser"
- Add `pages: [92]` configuration
- Create parser function `parse_creature_size_table()` in `text_table_parser.py`
- Handle two-column layout (Size | Space headers with 6 data rows)
- Validate extraction matches current reference data

---

### 3. cantrip_damage ❌ REMOVE

**Status:** **NOT FOUND in PDF**
**Investigation:** Searched entire 403-page PDF for cantrip damage scaling
**Recommendation:** **DECOMMISSION - Remove from tables.json**

**Why it doesn't exist:**
- Cantrip damage scaling is mentioned in **individual spell descriptions** (e.g., Fire Bolt, Ray of Frost)
- No standalone "Cantrip Damage" table exists in SRD 5.1
- This is a **convenience table** created to summarize a rule pattern
- Rule: "The spell's damage increases by [X] when you reach 5th level (2 dice), 11th level (3 dice), and 17th level (4 dice)"

**Current reference data:**
```
Character Level | Damage
1st-4th         | 1 die
5th-10th        | 2 dice
11th-16th       | 3 dice
17th-20th       | 4 dice
```

**This is derived from:**
- Pattern observed across damage cantrips (Fire Bolt, Ray of Frost, Eldritch Blast, etc.)
- Mentioned in spell descriptions but never as a standalone table
- Not official SRD content - it's a summary/convenience reference

**Action:**
- **Remove** from `table_metadata.py` entirely
- **Remove** from `reference_data.py`
- **Document removal** in CHANGELOG for downstream consumers (Blackmoor)
- **Alternative:** Spell records already contain scaling information in their `scaling` field

**Impact Assessment:**
- Low impact: Spell scaling data already exists in individual spell records
- Downstream tools (Blackmoor) should use spell-level scaling data instead
- This table was convenience/summary, not source data

---

### 4. spell_slots_by_level ❌ KEEP AS REFERENCE (or REMOVE)

**Status:** **NOT FOUND as standalone table**
**Investigation:** Checked spellcasting section (pages 100-104) and class tables (pages 8-55)
**Recommendation:** **KEEP as reference OR REMOVE** (decision needed)

**Why it doesn't exist standalone:**
- Spell slot progression appears in **every full caster class progression table**
- Exists in: Bard, Cleric, Druid, Sorcerer, Wizard class tables
- Not presented as standalone table in spellcasting section
- This is **derived data** - extracted from class tables, not a source table

**Current reference data:**
```
Level | 1st | 2nd | 3rd | 4th | 5th | 6th | 7th | 8th | 9th | Cantrips
1     | 2   | 0   | 0   | 0   | 0   | 0   | 0   | 0   | 0   | varies
...
20    | 4   | 3   | 3   | 3   | 3   | 2   | 2   | 1   | 1   | varies
```

**This is derived from:**
- Bard, Cleric, Druid, Sorcerer, Wizard class progression tables
- Each class has identical spell slot progression (full caster)
- Half-casters (Paladin, Ranger) have different progression
- Already extracted via CLASS_PROGRESSIONS tables

**Options:**

**Option A: KEEP as reference (convenience table)**
- Useful for quick lookup of full caster spell slots
- Avoids needing to check 5 different class tables
- Mark as `source: "derived"` since it's extracted from class tables
- Keep current `pattern_type: "reference"`
- Update notes: "Full caster spell slot progression - derived from class tables, not standalone SRD table"

**Option B: REMOVE (purist approach)**
- Data already exists in class progression tables
- Redundant with CLASS_PROGRESSIONS
- Not a source table from SRD
- Users can reference any full caster class for spell slots

**Recommendation:** **Option A - KEEP** with updated metadata
- Change `source` from "reference" to "derived"
- Update `notes` to clarify it's derived from class tables
- Useful convenience table that's commonly referenced
- Low maintenance burden (validated against class tables)

---

## Summary of Actions

### Extract from PDF (2 tables)
1. ✅ **travel_pace** - Page 84
2. ✅ **creature_size** - Page 92

### Decommission (1 table)
3. ❌ **cantrip_damage** - Remove entirely (not in SRD, convenience table)

### Update Metadata (1 table)
4. 🔄 **spell_slots_by_level** - Keep as reference, update `source` to "derived"

---

## Migration Plan

### Phase 1: Extract travel_pace and creature_size
1. Create parser functions in `text_table_parser.py`
2. Update `table_metadata.py` configurations
3. Validate extractions match reference data
4. Add tests to ensure extraction stability

### Phase 2: Remove cantrip_damage
1. Remove from `table_metadata.py`
2. Remove from `reference_data.py`
3. Update build process to skip this table
4. Add deprecation notice to CHANGELOG

### Phase 3: Update spell_slots_by_level
1. Change `source: "reference"` to `source: "derived"`
2. Update notes to clarify derivation source
3. Consider validation against class tables

### Phase 4: Documentation
1. Update ROADMAP.md with findings
2. Create CHANGELOG entry for removed tables
3. Document for downstream consumers (Blackmoor):
   - `cantrip_damage` removed - use spell-level `scaling` field instead
   - `travel_pace` now extracted from PDF (transparent change)
   - `creature_size` now extracted from PDF (transparent change)
   - `spell_slots_by_level` still available but marked as derived data

---

## Downstream Impact (Blackmoor)

**Breaking Changes:**
- ❌ `cantrip_damage` table removed from `tables.json`

**Mitigation:**
- Spell records already contain `scaling` field with damage progression
- Alternative: Query spells with `level: 0` and check `scaling.type: "character_level"`
- Example: Fire Bolt has `scaling.milestones: [5, 11, 17]` with damage increases

**Non-Breaking Changes:**
- ✅ `travel_pace` - Still available, now PDF-extracted (no schema change)
- ✅ `creature_size` - Still available, now PDF-extracted (no schema change)
- ✅ `spell_slots_by_level` - Still available, metadata updated (no schema change)

---

## Conclusion

**v0.9.7 delivers:**
- 2 tables migrated from reference to PDF extraction (travel_pace, creature_size)
- 1 convenience table removed (cantrip_damage) - not SRD content
- 1 reference table reclassified as derived (spell_slots_by_level)
- Clear documentation for downstream consumers

**Alignment with SRD-first principle:**
- Extract what's in the PDF
- Remove what's not in the PDF
- Document what's derived from the PDF
- Stay true to source material
