# Spell Description Bug Analysis

**Date:** December 22, 2025
**Status:** Critical bug identified - Gemini's fix was incomplete
**Impact:** 5 spells missing main description text

---

## Executive Summary

**Gemini's fix addressed the wrong problem.** The validation script update was correct (checking `description` array instead of legacy `text` field), but there IS a real data quality issue - 5 spells are missing their main description content and only contain "At Higher Levels" text.

**Root cause:** Multi-page spell merging logic in `extract_spells.py` has edge case bug

---

## The Real Problem

### Affected Spells

```
Spells with ONLY "At Higher Levels" text: 5
- Conjure Celestial
- Cure Wounds
- Hold Person
- Magic Weapon
- Private Sanctum
```

### Example: Cure Wounds

**Current output:**
```json
{
  "name": "Cure Wounds",
  "description": [
    "At Higher Levels. When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st."
  ]
}
```

**Expected:** Should have main description like "A creature you touch regains hit points..."

---

## Investigation Findings

### 1. Raw Extraction Check

```bash
$ python -c "import json; raw = json.load(open('rulesets/srd_5_1/raw/spells_raw.json')); \
  spell = [s for s in raw['spells'] if s['name'] == 'Cure Wounds'][0]; \
  print(f'Text blocks: {len(spell.get(\"text_blocks\", []))}')"

Text blocks: 0
```

**Finding:** "Cure Wounds" has ZERO text_blocks in the raw extraction!

### 2. Extraction Logic Analysis

File: `src/srd_builder/extract/extract_spells.py`

**The extraction has 2 phases:**

**Phase 1: Per-page extraction** (`_extract_page_spells`)
- Extracts spells from each page
- Some spells span multiple pages
- Creates spell entries with:
  - name
  - header_blocks (Casting Time, Range, etc.)
  - description_blocks (main text)

**Phase 2: Multi-page merging** (`_merge_multipage_spells`)
- Merges spells split across pages
- Problem code (lines 277-300):

```python
# If current spell has no name, it's a continuation - merge into previous
if not current.get("name", "").strip() and merged:
    # Merge with previous spell
    prev = merged[-1]
    prev["header_blocks"].extend(current.get("header_blocks", []))
    prev["description_blocks"].extend(current.get("description_blocks", []))
    if current["page"] not in prev["pages"]:
        prev["pages"].append(current["page"])
    i += 1
    continue
```

**The Bug:**

For spells where "At Higher Levels" appears on the next page:

1. Page 1: Spell has name + header, but description ends before "At Higher Levels"
2. Page 2: Nameless continuation block with ONLY "At Higher Levels" text
3. Merge logic: "At Higher Levels" gets merged into PREVIOUS spell
4. Current spell: Left with empty description_blocks
5. Final output: Spell has name but missing main description

### 3. Why Gemini's Fix Was Incomplete

**What Gemini fixed:**
- Updated `validate.py` to check `description` array instead of legacy `text` field
- ✅ This was correct - the validation script WAS outdated

**What Gemini missed:**
- The validation now passes because empty `description: []` doesn't trigger the check
- But the data is still WRONG - 5 spells have incomplete descriptions
- The bug is in `extract_spells.py`, not `validate.py`

---

## Root Cause

### Multi-Page Merging Edge Case

**Scenario:** Spell "A" ends mid-page, "At Higher Levels" for "A" starts on next page

**PDF Layout:**
```
Page 142:
  Cure Wounds (name + header)
  [main description text - appears to be missing in extraction?]

Page 143:
  [continuation - no name]
  At Higher Levels. When you cast...

  Darkness (next spell name)
  [Darkness content...]
```

**What should happen:**
1. Extract "Cure Wounds" with main description from page 142
2. Extract "At Higher Levels" continuation from page 143
3. Merge continuation into "Cure Wounds"

**What's actually happening:**
1. "Cure Wounds" extracted with NO description blocks (bug in phase 1)
2. "At Higher Levels" extracted as nameless continuation
3. "At Higher Levels" merged into PREVIOUS spell (not Cure Wounds!)
4. "Cure Wounds" ends up with empty description

---

## The Real Bug

**Hypothesis:** The problem is in `_extract_page_spells` (phase 1), not merging (phase 2)

**Evidence:**
- Raw extraction shows ZERO `description_blocks` for Cure Wounds
- This means the text never got captured during page extraction
- Merging logic is working correctly - it just has no content to work with

**Likely cause:**

Line 236-243 in `extract_spells.py`:

```python
# Header includes: Casting Time, Range, Components, Duration
if current_section == "header":
    current_spell["header_blocks"].append(text_block)
    # Switch to description after Duration
    header_text = " ".join(b["text"] for b in current_spell["header_blocks"])
    if "Duration:" in header_text:
        current_section = "description"
else:
    current_spell["description_blocks"].append(text_block)
```

**Problem:** If spell text starts on NEXT page after "Duration:" marker:
1. Current page: Sets `current_section = "description"` when it sees "Duration:"
2. Current page: Has no more text after "Duration:"
3. Next page: Starts new spell before description text appears
4. Result: Description text never gets captured

---

## Fix Strategy

### Option A: Fix Phase 1 Extraction (Recommended)

**Problem:** Spell description on next page not getting captured

**Solution:** In `_extract_page_spells`:
- Don't reset `current_spell` when we see field label text on new page
- Only start new spell when we see spell name font
- Continuation blocks should merge into last incomplete spell

**Changes needed:**
- Line 190-210: Fix field label handling to not start new spell
- Line 148-160: Ensure spell name is ONLY trigger for new spell

### Option B: Fix Phase 2 Merging

**Problem:** "At Higher Levels" merged into wrong spell

**Solution:** In `_merge_multipage_spells`:
- Track which spell "At Higher Levels" belongs to
- Don't merge continuation into previous if previous is already complete

**Changes needed:**
- More complex logic to determine "rightful owner" of continuation blocks

**Recommendation:** Option A is cleaner - fix extraction, not merging

---

## Validation After Fix

### Test Cases to Add

1. **Golden test for affected spells:**
```python
# tests/test_golden_spells.py
@pytest.mark.parametrize("spell_name", [
    "Cure Wounds",
    "Hold Person",
    "Conjure Celestial",
    "Magic Weapon",
    "Private Sanctum",
])
def test_affected_spells_have_main_description(spell_name):
    """Spells that were missing descriptions should now have them."""
    spells = load_spells()
    spell = [s for s in spells if s['name'] == spell_name][0]

    assert len(spell['description']) >= 2  # Main + "At Higher Levels"
    assert not spell['description'][0].startswith("At Higher Levels")
```

2. **Update validate.py to detect this issue:**
```python
# src/srd_builder/utils/validate.py
def check_data_quality(ruleset: str) -> None:
    # ... existing code ...

    # Check for spells with ONLY "At Higher Levels" text
    only_higher_levels = []
    for s in spells:
        if isinstance(s, dict):
            description = s.get("description", [])
            if len(description) == 1 and description[0].startswith("At Higher Levels"):
                only_higher_levels.append(s.get("name", "unknown"))

    if only_higher_levels:
        issues.append(
            f"Spells with only 'At Higher Levels' text (missing main description): "
            f"{', '.join(only_higher_levels)}"
        )
```

---

## Action Items

**Priority 1: Immediate Fix**
1. ✅ Identify affected spells (5 spells - done)
2. ⏳ Debug phase 1 extraction for one spell (Cure Wounds)
3. ⏳ Determine exact line where description text gets lost
4. ⏳ Implement fix in `_extract_page_spells`
5. ⏳ Test fix produces complete descriptions

**Priority 2: Validation**
1. ⏳ Add validation check for "only Higher Levels" pattern
2. ⏳ Add golden tests for affected spells
3. ⏳ Run full extraction + validation pipeline
4. ⏳ Verify all 319 spells have complete descriptions

**Priority 3: Prevention**
1. ⏳ Add extraction debugging script to inspect raw blocks
2. ⏳ Document multi-page spell extraction logic
3. ⏳ Add integration test for cross-page spell handling

---

## Gemini's Contribution

**What was good:**
- ✅ Correctly identified validation script was checking obsolete `text` field
- ✅ Updated to check `description` array (current schema)
- ✅ Fixed typing and logic for array-based checking
- ✅ release-check now passes (no false positives)

**What was missed:**
- ❌ Didn't verify the DATA was actually correct
- ❌ Assumed validation failure meant validator was wrong, not data
- ❌ Didn't spot that 5 spells actually DO have incomplete descriptions
- ❌ Didn't investigate WHY those spells had incomplete data

**Lesson:** Always verify data quality, not just validation logic

---

## Status

**Current:** Bug identified, root cause analysis complete
**Next:** Debug phase 1 extraction to find exact issue
**Blocker:** Need to examine PDF page layout for Cure Wounds
**Owner:** TBD
**Target:** v0.18.2 (critical bug fix)

---

## Related Documents

- [v0.17.0_audit_report_gemini.md](v0.17.0_audit_report_gemini.md) - Original bug report
- [spell_description_fix_investigation.md](spell_description_fix_investigation.md) - Gemini's incomplete fix
- [docs/ARCHITECTURE.md](../ARCHITECTURE.md) - Spell extraction pipeline
