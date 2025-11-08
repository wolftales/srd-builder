# Equipment Table Extraction Bugs

## Status: ✅ RESOLVED (2025-11-08)

All critical bugs have been fixed. Equipment assembly now produces complete data with all properties.

## Original Issue
Multiple equipment tables from v0.9.9 Part 1 were missing critical columns.

## Affected Tables

### 1. Armor Table (pages 63-64) - CRITICAL
**Extracted (5 columns):**
- Armor (name)
- Cost
- Armor Class (AC) - includes "(max X)" text that should be separate
- Stealth - but contains AC max bonus like "(max 2)"
- Weight - shows "—" (em-dash) for all items

**Expected (6 columns per SRD):**
- Armor
- Cost
- Armor Class (AC)
- Strength (**MISSING**)
- Stealth
- Weight (**MISSING** - shows placeholder)

### 2. Weapons Table (pages 65-66) - CRITICAL
**Extracted (4 columns):**
- Name
- Cost
- Damage
- Weight

**Expected (5 columns per SRD):**
- Name
- Cost
- Damage
- Weight
- Properties (**COMPLETELY MISSING**)

**Impact:** 37 weapons assembled but missing all properties (finesse, versatile, range, thrown, etc.)

### 3. Other Tables with Em-dash Issues
- **Tools**: Contains em-dash placeholders
- **Adventure Gear**: Contains em-dash placeholders
- **Tack/Harness/Vehicles**: Contains em-dash placeholders

## Impact Summary
**Equipment assembly creates 243 items but with major data loss:**

### Armor (13 items)
- ❌ Missing: Strength requirements (e.g., Str 13 for Chain mail, Str 15 for Plate)
- ❌ Missing: Weight values (all show —)
- ✅ Has: Names, cost, AC with dex bonus/max
- Old PyMuPDF had correct weights: Leather 10 lb, Chain shirt 20 lb, Chain mail 55 lb, Plate 65 lb

### Weapons (37 items)
- ❌ Missing: ALL properties (finesse, versatile, range, thrown, two-handed, loading, etc.)
- ✅ Has: Names, cost, damage, weight
- Old PyMuPDF had properties: Longsword (versatile), Dagger (finesse, light, thrown), etc.

### Overall
- **BLOCKING:** Cannot produce complete equipment dataset
- **Regression:** Old PyMuPDF extraction had more complete data
- **User Impact:** Missing critical gameplay properties (weapon properties, armor strength reqs)

## Root Cause
Table extraction (Part 1) from pages 63-64:
- Multi-page table with complex header
- Text-based parser may have misaligned columns
- Possible PDF rendering issue with table structure

## Workaround (Current)
- Equipment assembly skips em-dash weight values
- AC max bonus parsed from stealth column when detected

## Resolution Summary

### Fixes Applied (2025-11-08)

#### 1. Armor Table - Added Strength Column ✅
- **Changed:** `table_metadata.py` armor table from 5 to 6 columns
- **Added:** "Strength" column with boundary at offset 238
- **Result:** Heavy armor now shows strength requirements (Chain mail: Str 13, Splint/Plate: Str 15)

#### 2. Armor Table - Fixed Weight Column ✅
- **Changed:** Extended x_max from 300 to 560 to include weight column
- **Added:** Weight column boundary at offset 348
- **Result:** All 13 armor items now have accurate weight data (Chain shirt: 20 lb, Plate: 65 lb)

#### 3. Weapons Table - Added Properties Column ✅
- **Changed:** `table_metadata.py` weapons table from 4 to 5 columns
- **Added:** "Properties" column with boundary at offset 243
- **Result:** 33/37 weapons now have complete properties (Longsword: versatile, Dagger: finesse/light/thrown)

#### 4. Column Boundary Calculation ✅
- **Root Cause:** Column boundaries were treated as absolute x-positions instead of offsets from x_min
- **Fixed:** Recalculated all boundaries as offsets from x_min=52
- **Example:** x=145 → offset 93 (145-52)
- **Result:** Columns now split correctly at actual text positions

#### 5. Armor Name/Cost Boundary ✅
- **Problem:** 4-digit costs like "1,500 gp" were bleeding into name column
- **Fixed:** Adjusted boundary from offset 88 to 82 (before x=136)
- **Result:** "Plate 1,500" → "Plate" with cost "1,500 gp" correctly separated

#### 6. Assembly Code - Strength Column Parsing ✅
- **Changed:** `assemble_equipment.py` to read from actual Strength column
- **Added:** `strength_idx = col_map.get("strength", None)` to column mapping
- **Updated:** Parsing logic to check strength column first, stealth as fallback
- **Result:** Heavy armor strength requirements correctly parsed and populated

### Validation Results
- ✅ 243 equipment items assembled
- ✅ 13/13 armor with weight data (no more em-dash placeholders)
- ✅ 3/3 heavy armor with strength requirements
- ✅ 33/37 weapons with properties
- ✅ All tests passing (`pytest tests/test_json_sanity.py`)

### Sample Output
```json
// Chain mail (heavy armor)
{
  "name": "Chain mail",
  "armor_class": {"base": 16, "dex_bonus": false},
  "strength_req": 13,
  "weight_lb": 55.0,
  "stealth_disadvantage": true
}

// Longsword (martial melee weapon)
{
  "name": "Longsword",
  "damage": {"dice": "1d8", "type": "slashing"},
  "properties": ["versatile"],
  "versatile_damage": {"dice": "1d10"},
  "weight_lb": 3.0
}
```

### Files Modified
- `src/srd_builder/table_extraction/table_metadata.py`: Column definitions and boundaries
- `src/srd_builder/assemble_equipment.py`: Strength column parsing logic

### Commit
- SHA: 1682d6c
- Message: "fix: correct armor and weapons table column boundaries"

## References
- SRD pages 63-64: Armor table
- SRD pages 65-66: Weapons table
- Current extraction: `rulesets/srd_5_1/raw/tables_raw.json` (tables 31-32)
- Old working data: `dist/srd_5_1/equipment.json` (PyMuPDF extraction)
- Table extraction: `src/srd_builder/table_extraction/`
