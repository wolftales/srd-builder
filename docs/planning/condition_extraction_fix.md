# Condition Extraction Fix - Implementation Report
**Date:** December 21, 2025
**Status:** ✅ IMPLEMENTED & VALIDATED
**Version:** v0.10.0+

## Implementation Summary

**Completed:**
- ✅ Core fixes to `prose_extraction.py` (case-sensitivity + column-aware extraction)
- ✅ 6 unit tests in `test_prose_extraction.py` (all passing)
- ✅ 5 integration tests in `test_conditions_golden.py` (all passing)
- ✅ Inline documentation explaining case-sensitivity rationale
- ✅ All 15 conditions extracting cleanly (0 warnings)
- ✅ Implementation report created

**Pending:**
- ⏳ Diagnostic file cleanup (condition_blocks.json, etc.)
- ⏳ Final pre-commit validation
- ⏳ Commit staged changes

---

## Executive Summary

Fixed two critical bugs in condition extraction causing text to bleed across condition boundaries:

1. **Case-insensitive matching bug**: The word "incapacitated" in Grappled's description was incorrectly treated as the Incapacitated section header, causing Grappled's text to be truncated and merged into Incapacitated's section.

2. **Column ordering bug**: Two-column PDF layout caused text to interleave incorrectly. Reading order jumped between columns instead of reading left-column-first, resulting in sections receiving text from vertically-aligned but horizontally-distant sections (e.g., Prone receiving Blinded text).

**Impact:** All 15 conditions in Appendix PH-A (pages 358-359) now extract with clean boundaries and complete text.

---

## Changes Implemented

### Core Fix: [prose_extraction.py](../src/srd_builder/prose_extraction.py)

**1. Case-Sensitive Header Matching**
- Removed `re.IGNORECASE` flag from `split_by_known_headers()`
- Distinguishes section headers ("Incapacitated") from inline references ("incapacitated")
- Preserves valid cross-references like "is incapacitated (see the condition)"

**2. Column-Aware PDF Extraction**
- Added `_extract_text_with_columns()` method to `ProseExtractor` class
- Splits page at midpoint, sorts each column by Y-position independently
- Reading order: left column top-to-bottom, then right column top-to-bottom
- Prevents text bleeding across column boundaries

**3. Boundary Validation System**
- New `_validate_section_boundaries()` function with optional validation
- Detects cross-contamination (one section containing another's header)
- Case-sensitive detection ignores lowercase references
- Warns on abnormally long sections (>2000 chars, likely merged)

### Quality Assurance: [test_prose_extraction.py](../tests/test_prose_extraction.py)

**6 Regression Tests:**
- Cross-reference handling (Grappled→Incapacitated)
- Boundary validation detection
- Case-sensitive vs case-insensitive matching
- Lowercase reference tolerance
- Capitalized contamination detection
- Multiple references in single section

### Developer Tools

**Diagnostic Scripts:**
- `scripts/diagnose_condition_extraction.py` - Multi-mode extraction analyzer
- `scripts/debug_condition_order.py` - PDF header position mapper
- `scripts/analyze_header_patterns.py` - Font metadata analyzer

**Investigation Artifacts:**
- `condition_blocks.json` - Raw PDF block positions
- `condition_diagnostic_output.txt` - Diagnostic run output

---

## Recommended Next Steps

### **Immediate (Pre-Merge)**

**1. Validate Implementation**
```bash
pytest -q tests/test_prose_extraction.py
pytest -q  # Full test suite
```
**Action:** Confirm all tests pass, especially new regression tests
**Priority:** CRITICAL
**Effort:** 2 minutes

**2. Build Pipeline Validation**
```bash
python -m srd_builder.build rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf
```
**Action:** Verify all 15 conditions extract cleanly without warnings
**Priority:** CRITICAL
**Effort:** 5 minutes

**3. Review Diagnostic Files**
**Action:** Decide whether to keep, gitignore, or delete:
- `condition_blocks.json`
- `condition_diagnostic_output.txt`
- `scripts/diagnose_condition_extraction.py`
- `scripts/debug_condition_order.py`
- `scripts/analyze_header_patterns.py`

**Recommendation:** Move to `.gitignore` or archive if investigation complete
**Priority:** HIGH
**Effort:** 5 minutes

### **High Priority (Post-Merge)**

**4. Add Integration Test**
```python
# tests/test_conditions_golden.py
def test_all_conditions_extract_cleanly():
    """Validate all 15 conditions extract without cross-contamination."""
    pdf_path = Path("rulesets/srd_5_1/raw/SRD_CC_v5.1.pdf")
    result = extract_conditions(pdf_path)

    # All 15 conditions present
    assert len(result["conditions"]) == 15

    # No warnings about cross-contamination
    assert result["_meta"]["total_warnings"] == 0

    # Validate specific known boundaries
    grappled = next(c for c in result["conditions"] if c["name"] == "Grappled")
    assert "reach of the grappler" in grappled["raw_text"]
    assert "Incapacitated" not in grappled["raw_text"]
```
**Priority:** HIGH
**Effort:** 30 minutes

**5. Document Case-Sensitivity Decision**
**Action:** Add inline comments explaining the case-sensitive choice:
```python
# Use case-sensitive matching to avoid matching references like
# "incapacitated" in other conditions' text vs header "Incapacitated"
# This is critical because D&D conditions frequently reference each other
# (e.g., "The grappler is incapacitated" in Grappled condition)
pattern = rf"\b{re.escape(header)}\b"
match = re.search(pattern, cleaned_text)
```
**Priority:** HIGH
**Effort:** 10 minutes

### **Medium Priority (Future Enhancement)**

**6. Parameterize Column Detection**
```python
class ProseExtractor:
    def __init__(
        self,
        ...,
        column_split_ratio: float = 0.5,  # Default: 50% split
    ):
```
**Action:** Make column split point configurable for different PDF layouts
**Priority:** MEDIUM
**Effort:** 1 hour
**Trigger:** If other prose sections (diseases, madness) need different splits

**7. Enhance Diagnostic Script**
```python
# scripts/diagnose_condition_extraction.py
try:
    import fitz
except ModuleNotFoundError:
    print("ERROR: PyMuPDF not installed. Install with: pip install PyMuPDF")
    sys.exit(1)
```
**Action:** Add graceful error handling for missing dependencies
**Priority:** MEDIUM
**Effort:** 15 minutes

**8. Add Extraction Quality Metrics**
```python
payload["stats"]["extraction_quality"] = {
    "sections_with_warnings": sum(1 for c in conditions if c.get("warnings")),
    "avg_section_length": sum(len(c["raw_text"]) for c in conditions) / len(conditions),
    "boundary_validation_enabled": True
}
```
**Action:** Track extraction quality metrics in build output
**Priority:** MEDIUM
**Effort:** 30 minutes

### **Low Priority (Nice to Have)**

**9. Performance Profiling**
**Action:** Measure extraction time before/after column-aware extraction
**Priority:** LOW
**Effort:** 30 minutes
**Trigger:** If extraction becomes noticeably slower

**10. Extend Framework Documentation**
**Action:** Update `docs/PROSE_EXTRACTION_FRAMEWORK.md` with:
- Column-aware extraction pattern
- Boundary validation best practices
- Case-sensitivity considerations
**Priority:** LOW
**Effort:** 1 hour

---

## Risk Assessment

**Low Risk** - Changes are well-isolated:
- ✅ Backward compatible (no API changes)
- ✅ Comprehensive test coverage (6 regression tests)
- ✅ Only affects prose extraction (conditions, future diseases/madness)
- ✅ Diagnostic tools available if issues arise

**Potential Issues:**
- Column split at 50% may not work for all PDF layouts (monitor when extracting diseases/madness)
- Case-sensitive matching assumes consistent PDF capitalization (validated for SRD 5.1)

---

## Success Criteria

**Pre-Merge:**
- [x] All tests pass (`pytest -q`) - 11/11 condition tests passing
- [x] Full build completes without errors
- [x] All 15 conditions extract cleanly - validated via integration test
- [x] No cross-contamination warnings - 0 warnings in extraction

**Post-Merge (within 1 week):**
- [x] Integration test added and passing - `tests/test_conditions_golden.py` (5 tests)
- [x] Case-sensitivity rationale documented in code - added detailed inline comments
- [ ] Diagnostic files archived or gitignored - pending decision

**Future (v0.11.0+):**
- [ ] Column detection validated with diseases/madness extraction
- [ ] Quality metrics integrated into build pipeline

---

## Contact & Questions

**Questions about this fix?**
- Review test cases in `tests/test_prose_extraction.py`
- Run diagnostic script: `python scripts/diagnose_condition_extraction.py`
- Check `docs/PROSE_EXTRACTION_FRAMEWORK.md`

**Regression concerns?**
- All changes affect only `prose_extraction.py` and conditions
- Monsters, spells, equipment, tables unaffected
- Rollback: revert `split_by_known_headers()` to add back `re.IGNORECASE`
