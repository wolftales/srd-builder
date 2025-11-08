# Equipment Table Extraction Bugs

## Issue
Multiple equipment tables from v0.9.9 Part 1 are missing critical columns.

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

## Proper Fix (Required for v0.9.9 completion)

### Priority 1: Weapons Properties
1. Re-extract weapons table to capture Properties column
2. Verify: Name | Cost | Damage | Weight | Properties (5 columns)
3. Test: Longsword has "Versatile (1d10)", Dagger has "Finesse, light, thrown (range 20/60)"

### Priority 2: Armor Strength & Weight
1. Re-extract armor table to capture all 6 columns
2. Verify: Armor | Cost | AC | Strength | Stealth | Weight
3. Test: Chain mail has Str 13, weights populated

### Priority 3: Em-dash Cleanup
1. Review why tools/adventure_gear/tack have em-dash instead of actual data
2. Validate against SRD source

### Process
1. Investigate table extraction code (table_extraction/)
2. Check if multi-column spans or page breaks cause issues
3. May need manual table coordinate adjustment or parser fixes
4. Re-run table extraction: `python -m srd_builder.build --tables-only`
5. Validate with test suite
6. Re-run full build to regenerate equipment.json

## References
- SRD pages 63-64: Armor table
- SRD pages 65-66: Weapons table
- Current extraction: `rulesets/srd_5_1/raw/tables_raw.json` (tables 31-32)
- Old working data: `dist/srd_5_1/equipment.json` (PyMuPDF extraction)
- Table extraction: `src/srd_builder/table_extraction/`
