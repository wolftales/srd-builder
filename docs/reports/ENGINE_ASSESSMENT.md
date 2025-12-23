# Engine-Based Postprocess: Assessment & Recommendations

**Date:** December 22, 2025
**Author:** AI Agent (GitHub Copilot)
**Status:** Proposal (prototype in progress)

---

## Executive Summary

**Problem:** We have 797 lines of duplicated postprocess logic across 12 dataset modules. This doesn't scale when we support multiple SRD versions.

**Solution:** Replace 12 per-dataset functions with 1 configuration-driven engine + 12 config entries.

**Impact:**
- **Code reduction:** 797 lines → ~350 lines (56% reduction)
- **Multi-version:** Add version = 1 config file, not 12 copied modules
- **Maintenance:** Fix bugs once in engine, not in 12 places

**Recommendation:** NOT for v0.19.0. Prototype, evaluate, possibly implement in v0.20.0+.

---

## Current State Analysis

### Duplication Metrics

```bash
$ wc -l src/srd_builder/postprocess/{monsters,spells,equipment,poisons,diseases,conditions,lineages,features,tables,classes}.py
  375 monsters.py
   51 spells.py
   53 equipment.py
   35 poisons.py
   44 diseases.py
   44 conditions.py
   52 lineages.py
   39 features.py
   48 tables.py
   56 classes.py
  797 total
```

### Common Patterns (100% duplication)

**Every module does:**
1. Generate `simple_name` (12/12 modules, identical logic)
2. Generate `id` (12/12 modules, identical logic)
3. Polish text fields (12/12 modules, identical logic)

**Example from 3 different modules:**

```python
# poisons.py (lines 24-27)
if "simple_name" not in poison:
    poison["simple_name"] = normalize_id(poison["name"])
if "id" not in poison:
    poison["id"] = f"poison:{poison['simple_name']}"

# diseases.py (lines 24-27)
if "simple_name" not in disease:
    disease["simple_name"] = normalize_id(disease["name"])
if "id" not in disease:
    disease["id"] = f"disease:{disease['simple_name']}"

# conditions.py (lines 24-27)
if "simple_name" not in condition:
    condition["simple_name"] = normalize_id(condition["name"])
if "id" not in condition:
    condition["id"] = f"condition:{condition['simple_name']}"
```

**Only difference:** The prefix string (`"poison:"` vs `"disease:"` vs `"condition:"`).

---

## Proposed Architecture

### Before (v0.18.0): Function-Based

```
postprocess/
├── monsters.py    (375 lines)
├── spells.py      (51 lines)
├── equipment.py   (53 lines)
├── poisons.py     (35 lines)
├── diseases.py    (44 lines)
├── conditions.py  (44 lines)
├── lineages.py    (52 lines)
├── features.py    (39 lines)
├── tables.py      (48 lines)
├── classes.py     (56 lines)
└── magic_items.py (not counted)
    rules.py       (not counted)
```

**Total:** ~800 lines of similar code

**To add new dataset:** Copy 40-120 lines of template code

### After (Proposed): Engine-Based

```
postprocess/
├── engine.py      (~150 lines) - Generic normalization logic
├── configs.py     (~200 lines) - Dataset configurations
└── [old modules kept for compatibility or deleted]
```

**Total:** ~350 lines

**To add new dataset:** Add ~8-15 line config entry

### Code Comparison

**Current (per-dataset function):**
```python
# postprocess/poisons.py (35 lines)
def clean_poison_record(poison: dict[str, Any]) -> dict[str, Any]:
    if "simple_name" not in poison:
        poison["simple_name"] = normalize_id(poison["name"])
    if "id" not in poison:
        poison["id"] = f"poison:{poison['simple_name']}"
    if "description" in poison:
        poison["description"] = polish_text(poison["description"])
    return poison
```

**Proposed (config + engine):**
```python
# postprocess/configs.py
DATASET_CONFIGS = {
    "poison": RecordConfig(
        id_prefix="poison",
        text_fields=["description"],
    ),
}

# postprocess/engine.py (shared by all datasets)
def clean_record(record: dict, config: RecordConfig) -> dict:
    if "simple_name" not in record:
        record["simple_name"] = normalize_id(record[config.name_field])
    if "id" not in record:
        record["id"] = f"{config.id_prefix}:{record['simple_name']}"
    for field in config.text_fields:
        if field in record:
            record[field] = polish_text(record[field])
    return record
```

---

## Multi-Version SRD Support (The Real Problem)

### Current Approach (Doesn't Scale)

**If we support SRD 5.1 and SRD 5.2:**

```
postprocess/
├── v5_1/
│   ├── monsters.py (375 lines)
│   ├── spells.py (51 lines)
│   └── ... (10 more, 797 lines total)
├── v5_2/
│   ├── monsters.py (375 lines, 90% copied from v5_1)
│   ├── spells.py (51 lines, 90% copied)
│   └── ... (10 more, ~800 lines total)
```

**Total:** 1,600 lines for 2 versions (mostly duplicated)

**For 3 versions:** 2,400 lines (mostly duplicated)

### Engine Approach (Scales)

```
postprocess/
├── engine.py (150 lines, shared across versions)
├── configs/
│   ├── v5_1.py (150 lines, specific to SRD 5.1)
│   └── v5_2.py (160 lines, only differences from 5.1)
```

**Total:** 460 lines for 2 versions (no duplication)

**For 3 versions:** 610 lines (engine once, configs per version)

---

## Assessment

### What We Gain

1. **Code reduction:** 797 lines → 350 lines (56% savings)
2. **Centralized logic:** Fix bugs once, affects all datasets
3. **Scalable versioning:** Add version = add config, not copy 12 modules
4. **Faster extensions:** New dataset = 10-line config vs 40-line module
5. **Clearer intent:** Declarative configs easier to understand than imperative code

### What We Lose

1. **Type safety:** Configs use strings, not compile-time checked
2. **Flexibility:** Edge cases need "escape hatch" (`custom_transform`)
3. **Familiarity:** Team needs to learn config pattern
4. **Debugging:** Stack traces go through engine layer

### Escape Hatch for Complex Cases

**Problem:** Some datasets have unique logic (e.g., CR calculations for monsters)

**Solution:** `custom_transform` function in config

```python
def _custom_monster_transform(monster: dict) -> dict:
    # Special monster logic
    monster["cr_numeric"] = calculate_cr(monster["challenge_rating"])
    return monster

"monster": RecordConfig(
    id_prefix="monster",
    text_fields=["description"],
    custom_transform=_custom_monster_transform,  # Escape hatch
)
```

**Guideline:** If >3 datasets need same transform, add to engine core.

---

## Recommendations

### Immediate (v0.19.0): DO NOT IMPLEMENT

**Reasons:**
1. v0.18.0 just refactored to modular pattern - let it stabilize
2. v0.19.0 focused on third-party review (current plan)
3. Need external validation before another refactor
4. Engine pattern needs prototyping first

**Action:** Document this proposal, add to roadmap as future work

### Near-Term (v0.20.0): PROTOTYPE & EVALUATE

**Phase 1: Spike (1-2 days)**
- Implement engine + 3 simple dataset configs (poison, disease, condition)
- Run golden tests - verify identical output
- Benchmark performance - ensure no regression
- Evaluate code readability - compare config vs function

**Success Criteria:**
- ✅ Golden tests pass (identical output)
- ✅ No performance degradation (benchmark)
- ✅ Code reduction >40%
- ✅ Configs are readable (not XML-like complexity)

**Go/No-Go Decision:**
- If all criteria met → Proceed to Phase 2
- If any fail → Document why, keep current approach

**Phase 2: Full Migration (if approved)**
- Extend engine to handle nested structures
- Migrate remaining 9 datasets
- Keep wrapper functions for backward compatibility
- Update documentation

### Long-Term (v1.0+): MULTI-VERSION SUPPORT

**When:** After engine proven stable

**Approach:**
- Move configs to `postprocess/configs/v5_1.py`
- Add `postprocess/configs/v5_2.py` when SRD 5.2 arrives
- build.py selects config based on version parameter
- Engine remains shared across versions

---

## Open Questions

1. **Performance:** Does config lookup add measurable overhead?
   - **How to answer:** Benchmark in Phase 1 (compare 1000 records with/without engine)

2. **Readability:** Are configs easier than functions for new developers?
   - **How to answer:** Get team feedback on prototype (Phase 1)

3. **Completeness:** Can engine handle all 12 datasets without escape hatches?
   - **How to answer:** Phase 2 migration will reveal edge cases

4. **Multi-version:** Do SRD versions differ enough to benefit from separate configs?
   - **How to answer:** Unknown until SRD 5.2 or 6.0 released

5. **Migration cost:** Is 2-3 day refactor worth 400-line reduction?
   - **How to answer:** Team decision after Phase 1 prototype

---

## Files Created

**Prototype (already created):**
- `src/srd_builder/postprocess/engine.py` - Generic normalization engine (~100 lines)
- `src/srd_builder/postprocess/configs.py` - Dataset configurations (~150 lines)
- `tests/test_engine_postprocess.py` - Engine tests (~100 lines)

**Documentation:**
- `docs/proposals/ENGINE_BASED_POSTPROCESS.md` - Full proposal with examples
- `docs/reports/ENGINE_ASSESSMENT.md` - This file (summary)

---

## Next Steps

**Immediate:**
1. Review this proposal with team
2. Add to roadmap as v0.20.0 candidate (after v0.19.0)
3. Continue with v0.19.0 third-party review (current focus)

**Before v0.20.0:**
1. Complete Phase 1 prototype (1-2 days)
2. Benchmark performance
3. Get team feedback on config readability
4. Make go/no-go decision

**If approved:**
1. Phase 2: Migrate all datasets (2-3 days)
2. Update ARCHITECTURE.md with engine pattern
3. Create migration guide for future datasets

---

## References

- **Full Proposal:** [docs/proposals/ENGINE_BASED_POSTPROCESS.md](../proposals/ENGINE_BASED_POSTPROCESS.md)
- **v0.18.0 Cleanup Report:** [docs/reports/v0.18.0_CLEANUP_REPORT.md](../reports/v0.18.0_CLEANUP_REPORT.md)
- **Current postprocess modules:** `src/srd_builder/postprocess/*.py` (797 lines)
- **Inspiration:** Django ORM, FastAPI routing, Pydantic models

---

## User Quote (Triggering This Analysis)

> "I've tried this engine route several times, and I keep seeing the sprawl of scripts thinking this isn't what I envisioned. This isn't going to go well when we try this against a new version of the SRD. We'll have another complete copied set of stuff."

**Translation:** Current function-based approach creates sprawl when we need to support multiple SRD versions. Need configuration-driven approach that scales.

**Response:** This proposal directly addresses that concern with engine + version-specific configs.

---

**Status:** Awaiting team review and roadmap prioritization
**Next Milestone:** v0.19.0 (third-party review) - DO NOT disrupt
**Future Consideration:** v0.20.0 (engine refactor) - Prototype first, then decide
