# Cruft Audit - October 30, 2025

## 🗑️ Potential Cruft to Clean

### Documentation Files (docs/)

**OUTDATED - Can Delete:**
1. ✅ `KNOWN_ISSUES.md` - Animated Armor issue is FIXED, other issues resolved
2. ✅ `EXTRACTION_COMPARISON.md` - Pre-v0.3.0 design doc, superseded by ROADMAP
3. ✅ `Extraction_Solution_Plan.md` - Original extraction plan, completed
4. ✅ `PHASE2_VICTORY.md` - v0.3.0 celebration doc, historical
5. ✅ `GEMINI_PHASE1_REVIEW.md` - AI review notes, historical
6. ✅ `GEMINI_REVIEW_BRIEF.md` - AI review setup, historical
7. ✅ `blackmoor_comparison.txt` - Raw text output, replaced by BLACKMOOR_COMPARISON.md
8. ✅ `quality_report_v0.3.3.txt` - Old quality report, replaced by live validation

**KEEP - Still Relevant:**
- `ROADMAP.md` - Current project roadmap ✅
- `INTEGRATION.md` - Blackmoor integration strategy ✅
- `COVERAGE_ANALYSIS.md` - Coverage metrics (could update for v0.4.1)
- `MONSTER_COUNT_INVESTIGATION.md` - Resolved 296 vs 319 question
- `BLACKMOOR_COMPARISON.md` - Comparison with Blackmoor parser

**MOVE TO archive/ OR docs/historical/:**
- All GEMINI_* files
- All PHASE* files
- Extraction_Solution_Plan.md
- EXTRACTION_COMPARISON.md

### Scripts (scripts/)

**KEEP - Useful:**
- ✅ `analyze_reference.py` - Useful for comparing with other parsers
- ✅ `compare_with_blackmoor.py` - Active use for comparison
- ✅ `count_monsters_in_pdf.py` - Useful diagnostic (just fixed!)
- ✅ `coverage_report.py` - Generates coverage analysis
- ✅ `explore_pdf.py` - Useful for investigating PDFs
- ✅ `find_missing_monsters.py` - Useful for validation
- ✅ `quality_report.py` - Generates quality reports
- ✅ `smoke.sh` - Quick test script
- ✅ `release_check.sh` - Release validation

**MAYBE OBSOLETE:**
- `cleanup_cruft.sh` - Last used Oct 29, what does it do?

### External Files (docs/external/)
```
ls docs/external/
```
Need to check what's in here - reference files?

### Reference Files (docs/reference/)
```
ls docs/reference/
```
Are these still needed?

### Templates (docs/templates/)
```
ls docs/templates/
```
TEMPLATE_* files - are these up to date with v0.4.1 structure?

## 🧹 Cleanup Actions

### Immediate (Low Risk):
1. Delete outdated .txt files
2. Delete resolved KNOWN_ISSUES.md
3. Archive historical GEMINI/PHASE docs

### Review First:
1. Check cleanup_cruft.sh - what does it do?
2. Review docs/external/ contents
3. Review docs/reference/ contents
4. Update docs/templates/ to match v0.4.1 structured fields

### After v0.4.1 Release:
1. Create docs/archive/ for historical documents
2. Move pre-v0.4.0 planning docs to archive
3. Update README to reflect current state

## ✅ Quality Cleanup (Done):
1. ✅ Fixed test_build_pipeline mock
2. ✅ Removed hardcoded PDF paths
3. ✅ All 56 tests passing
4. ✅ No warnings in data
