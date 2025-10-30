# Known Issues & Edge Cases

This document tracks specific parsing oddities, edge cases, and deferred bugs that need attention in future versions. Unlike the ROADMAP (which tracks milestones), this is for **concrete technical debt** and **specific monster/entity problems**.

---

## 🐛 Active Issues

### Parser: Animated Armor (Ability Score Split)
**Affected Entity:** Animated Armor
**Version:** v0.3.0
**Status:** Deferred to v0.4.0

**Issue:**
Animated Armor has only 3 ability scores (STR, DEX, CON). The parser expects 6 abilities in a single line:
```
STR  DEX  CON  INT  WIS  CHA
21 (+5) 9 (-1) 15 (+2) 18 (+4) 15 (+2) 18 (+4)
```

But Animated Armor has values split across blocks:
```
STR    DEX    CON    INT  WIS  CHA
14 (+2) 11 (+0) 13 (+1)  1   1   1
```

**Impact:**
Parser may fail to extract ability scores or assign them incorrectly.

**Workaround:**
None yet. Current parser will likely fail or produce null ability_scores.

**Fix Strategy (v0.4.0):**
- Check if ability score line has fewer than 6 values
- Handle split formatting (3 normal, 3 minimal)
- Use font metadata to detect formatting differences
- May need special case for constructs/undead with reduced mental stats

**Reference:**
See extraction blocks for "Animated Armor" in `monsters_raw.json`

---

## 🔍 Under Investigation

### Multi-Column Text Flow
**Version:** v0.3.0
**Status:** Needs validation

**Issue:**
PDF uses two-column layout. Extraction sorts by (page, column, y-pos), but need to verify:
1. Column boundary detection (x > 306pt) is accurate
2. Blocks don't interleave between columns
3. Text flow is logical within each column

**Action Items:**
- Check monsters near column breaks
- Verify block ordering in `monsters_raw.json`
- Create column-flow test cases

---

## 📝 Deferred Enhancements

### Ability Score Short Name API Access
**Affected Field:** `ability_scores`
**Version:** v0.3.0
**Status:** Enhancement for v0.4.0

**Issue:**
Monster stat blocks use standardized short names (STR, DEX, CON, INT, WIS, CHA). Schema currently stores full names:
```json
{
  "ability_scores": {
    "strength": 21,
    "dexterity": 9,
    "constitution": 15,
    "intelligence": 18,
    "wisdom": 15,
    "charisma": 18
  }
}
```

**Enhancement:**
Support both short and full name access for convenience:
```python
monster["ability_scores"]["str"]  # shorthand access
monster["ability_scores"]["strength"]  # full name access
```

**Benefits:**
- More natural API for D&D conventions
- Shorter, cleaner client code
- Both names are standardized and universally recognized

**Implementation Options:**
1. Store both keys (redundant but simple)
2. Custom dict subclass with `__getitem__` override
3. Helper function for ability score access
4. Schema change to support both formats

**Decision:** Defer to v0.4.0 API design phase

---

### AC Detail Loss: "(natural armor)" Suffix
**Affected Field:** `armor_class`
**Version:** v0.3.0
**Status:** Deferred to v0.4.0

**Issue:**
Current parser extracts AC as string: `"17 (natural armor)"`.
Schema supports structured format:
```json
{
  "value": 17,
  "source": "natural armor"
}
```

**Impact:**
Data is present but not structured. Clients must parse string.

**Fix (v0.4.0):**
- Parse AC value and source separately
- Support multiple AC sources (e.g., "18 (natural armor, shield)")
- TODO comment added to parser

---

### HP Formula Extraction
**Affected Field:** `hit_points`
**Version:** v0.3.0
**Status:** Deferred to v0.4.0

**Issue:**
Current parser extracts HP as string: `"135 (18d10 + 36)"`.
Schema supports structured format:
```json
{
  "average": 135,
  "formula": "18d10+36"
}
```

**Impact:**
Data is present but not structured. Clients must parse string.

**Fix (v0.4.0):**
- Parse average HP and dice formula separately
- Validate formula matches average (±1 for rounding)
- TODO comment added to parser

---

## 🎯 Validation Gaps

### Reference Count Delta (296 vs 319)
**Version:** v0.3.0
**Status:** Validation framework complete, documentation pending

**Issue:**
External reference claims 319 monsters. We extract 296. Need to document the 23-entry delta.

**Current Status:**
- ✅ Validation framework confirms 296 is correct
- ✅ All 8 core categories complete
- ⏳ Need to list specific non-monster entries from reference

**Action Items (Post-v0.3.0):**
- Document 23 excluded entries with page numbers
- Examples: NPCs (page 60), appendices (post-394), conditions, chapter headers
- Create comparison report for transparency
- See ROADMAP > Validation Backlog for details

---

## 🧪 Test Coverage Gaps

### Extraction Tests Missing
**Version:** v0.3.0
**Status:** Extraction works, tests pending

**Missing Tests:**
- Single monster extraction (unit test)
- Category detection accuracy
- Column handling (multi-column flow)
- **Cross-page monsters (page breaks) - REGRESSION TEST NEEDED**
- Font pattern recognition (name detection, stat labels)

**Priority Test Cases:**
1. **Cross-page regression test** (HIGH PRIORITY)
   - Test monsters known to span pages: Deva (261-262), Solar, etc.
   - Verify block count remains high (50+ blocks for complex monsters)
   - Ensure traits/actions are extracted completely
   - Prevent regression of the page-boundary bug fixed in commit 7abeb74

2. **Known challenge monsters:**
   - Deva: Must have 70+ blocks, traits=[3], actions=[4]
   - Solar: Must span multiple pages with complete stat block
   - Animated Armor: 3 abilities edge case

**Action Items:**
- Create `tests/fixtures/extract/` with raw snapshots
- Add `tests/test_extract_basic.py`
- Add `tests/test_extract_cross_page.py` for page-spanning monsters
- Test edge cases identified above---

## 📋 How to Use This Document

**When adding an issue:**
1. Add to appropriate section (🐛 Active, 🔍 Investigation, 📝 Deferred, 🎯 Validation, 🧪 Tests)
2. Include: Affected entity/field, version discovered, current status
3. Describe issue clearly with examples
4. Note impact and workarounds if any
5. Outline fix strategy with target version

**When resolving an issue:**
1. Move to "Resolved" section at bottom (keep for history)
2. Note version resolved and commit/PR reference
3. Keep original description for context

**When to use KNOWN_ISSUES.md vs ROADMAP.md:**
- **KNOWN_ISSUES:** Specific bugs, edge cases, technical debt
- **ROADMAP:** Milestones, features, version planning

---

## ✅ Resolved Issues

### Extraction: Cross-Page Monster Handling ✅
**Version:** Fixed in v0.3.0 (commit 7abeb74)
**Affected:** Deva, Solar, and 23 other monsters

**Original Issue:**
Monsters spanning page boundaries were truncated. Extraction processed one page at a time, causing stat blocks to end prematurely at page breaks.

**Symptoms:**
- Deva: Only 28 blocks (missing traits/actions)
- Solar: Only 17 blocks
- 23 monsters total with <20 blocks
- Monsters showed 0 traits, 0 actions in parsed output

**Root Cause:**
`extract_monsters()` called `_extract_page_monsters()` per-page, detecting monster boundaries within each page. Monsters crossing pages were split incorrectly.

**Fix Applied:**
- Renamed `_extract_page_monsters` → `_extract_page_lines`
- Now collects ALL lines from ALL pages first
- Monster boundary detection runs on complete line set across pages
- Handles page breaks transparently

**Result:**
- ✅ All 296 monsters now have 20+ blocks (was 273 complete, 23 broken)
- ✅ Deva: 28 → 78 blocks, now includes 3 traits, 4 actions
- ✅ Solar: Complete stat block extraction
- ✅ Resolves Gemini YELLOW flag for multi-page handling

**Test Coverage:**
⚠️ NEEDS REGRESSION TEST - Add to `tests/test_extract_cross_page.py`

---

**Last Updated:** v0.3.0 (October 30, 2025)
