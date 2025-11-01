# Documentation Consolidation Plan

**Date:** November 1, 2025
**Goal:** Eliminate sprawl, keep only what's needed, stay lean

## 📊 Current State

**Total markdown files:** 30 files, 10,526 lines
**Problem:** Documentation is growing faster than code

### Largest Files (Top 10)
1. equipment_tables_plan/srd_equipment_strategic_plan.md (1272 lines)
2. archive/Extraction_Solution_Plan.md (732 lines)
3. equipment_tables_plan/gpt_action_plan.md (686 lines)
4. equipment_tables_plan/table_architecture_proposal.md (598 lines)
5. DATA_DICTIONARY.md (586 lines)
6. equipment_tables_plan/table_metadata_integration.md (579 lines)
7. external/blackmoor/blackmoor_srd_5_1_package review.md (480 lines)
8. SCHEMAS.md (467 lines)
9. ARCHITECTURE.md (444 lines)
10. equipment_tables_plan/schema_compromise_recommendation.md (433 lines)

## 🗑️ DELETE - Obsolete/Redundant

### Root Level
- **CRUFT_AUDIT.md** (92 lines) - This very doc makes it obsolete, delete after consolidation
- **CONTRIBUTING.md** - Empty or boilerplate? Check and delete if not needed

### docs/
- **GPT_REVIEW_equipment_status.md** (426 lines) - Historical GPT consultation, superseded by v0.5.0
- **PARKING_LOT.md** (173 lines) - Deferred features, merge into ROADMAP Future section
- **terminology.aliases.md** (213 lines) - Speculative design, not implemented, delete

### docs/equipment_tables_plan/ (ENTIRE FOLDER - 4353 lines!)
**Problem:** 6 planning documents totaling 4353 lines for equipment that's now DONE
- srd_equipment_strategic_plan.md (1272 lines) - Planning doc, work complete
- gpt_action_plan.md (686 lines) - Planning doc, work complete
- table_architecture_proposal.md (598 lines) - Planning doc, work complete
- table_metadata_integration.md (579 lines) - Future work, move to ROADMAP
- schema_compromise_recommendation.md (433 lines) - Historical, schema finalized
- collaborative_strategy_summary.md (385 lines) - Historical planning

**Action:** Delete entire folder, extract Phase 0.5 plan into ROADMAP

### docs/external/blackmoor/
- **blackmoor_srd_5_1_package review.md** (480 lines) - External review, move to archive
- Keep README_v1/v2 as reference

## 📦 ARCHIVE - Historical Value Only

Move to docs/archive/ (already exists):
- GPT_REVIEW_equipment_status.md → archive/
- equipment_tables_plan/ → archive/equipment_planning/
- PARKING_LOT.md → archive/

## 🔀 CONSOLIDATE - Merge & Simplify

### Merge v0.5.0 docs into ROADMAP
**Current:**
- v0.5.0_RELEASE_NOTES.md (312 lines)
- v0.5.0_TODO.md (185 lines)
- Total: 497 lines

**Action:**
1. Extract key points into ROADMAP.md under "v0.5.0 - COMPLETE" section
2. Move both files to archive/
3. Keep git tag v0.5.0 as source of truth

### Simplify SCHEMAS.md
**Current:** 467 lines with examples
**Action:** Keep schema documentation, remove redundant examples (schemas/ folder is source of truth)

### Simplify DATA_DICTIONARY.md
**Current:** 586 lines
**Action:** This should be AUTO-GENERATED from schemas, not manually maintained

## ✅ KEEP - Essential Documentation

### Root Level (User-Facing)
- **README.md** - Primary entry point ✅
- **LICENSE** - Legal requirement ✅
- **AGENTS.md** - Workflow guardrails ✅

### docs/ (Developer-Facing)
- **ROADMAP.md** - Project planning ✅
- **ARCHITECTURE.md** - System design ✅
- **SCHEMAS.md** - Schema documentation ✅
- **INTEGRATION.md** - Blackmoor integration ✅
- **BUNDLE_README.md** - Distribution package docs ✅

### docs/archive/
- Keep for historical reference, don't delete

### docs/external/
- **srd_cc_v5.1_rules_tabyltop.json** - Reference data ✅
- **blackmoor/README_v2.md** - Reference implementation ✅

### docs/templates/
- TEMPLATE_*.json - Schema examples ✅

## 🎯 Consolidation Actions

### Phase 1: Delete Obsolete (Safe)
```bash
# Delete completed planning docs
rm -rf docs/equipment_tables_plan/

# Delete speculative designs
rm docs/terminology.aliases.md
rm docs/GPT_REVIEW_equipment_status.md
rm docs/PARKING_LOT.md

# Delete this audit
rm CRUFT_AUDIT.md
```

**Savings:** ~5,000 lines removed

### Phase 2: Archive Historical
```bash
# Move v0.5.0 docs to archive
mv docs/v0.5.0_RELEASE_NOTES.md docs/archive/
mv docs/v0.5.0_TODO.md docs/archive/

# Create equipment planning archive
mkdir -p docs/archive/equipment_planning
# (but we deleted it in Phase 1, so skip)
```

### Phase 3: Update Core Docs
1. **ROADMAP.md** - Add v0.5.0 completion, extract Phase 0.5 planning
2. **README.md** - Update status, remove outdated references
3. **ARCHITECTURE.md** - Add ColumnMapper, update for v0.5.0

### Phase 4: Simplify (Future)
- Generate DATA_DICTIONARY.md from schemas (automation)
- Keep SCHEMAS.md concise, schemas/ folder is source of truth

## 📈 Before/After

### Before
```
docs/
├── ARCHITECTURE.md (444 lines)
├── BUNDLE_README.md (92 lines)
├── DATA_DICTIONARY.md (586 lines)
├── GPT_REVIEW_equipment_status.md (426 lines) ❌
├── INTEGRATION.md (155 lines)
├── PARKING_LOT.md (173 lines) ❌
├── ROADMAP.md (386 lines)
├── SCHEMAS.md (467 lines)
├── archive/ (2037 lines)
├── equipment_tables_plan/ (4353 lines) ❌
├── external/ (...)
├── templates/
├── terminology.aliases.md (213 lines) ❌
├── v0.5.0_RELEASE_NOTES.md (312 lines) → archive
└── v0.5.0_TODO.md (185 lines) → archive

Total: ~10,500 lines
```

### After
```
docs/
├── ARCHITECTURE.md (~450 lines)
├── BUNDLE_README.md (92 lines)
├── DATA_DICTIONARY.md (586 lines)
├── INTEGRATION.md (155 lines)
├── ROADMAP.md (~450 lines, updated)
├── SCHEMAS.md (~400 lines, simplified)
├── archive/ (~3000 lines, historical)
├── external/ (reference data)
└── templates/ (schema examples)

Total: ~5,100 lines (52% reduction)
```

## 🚦 Recommendation

**Execute Phase 1 immediately** - Delete 5,000 lines of obsolete planning docs

**Why it's safe:**
1. Equipment work is complete (v0.5.0 tagged)
2. Planning docs served their purpose
3. Git history preserves everything
4. Phase 0.5 plan can be extracted to ROADMAP (200 lines max)

**Keep lean principle:**
- Documentation should explain what exists, not plan what might exist
- Planning docs → delete after work complete
- Historical context → git history
- Active work → ROADMAP.md
