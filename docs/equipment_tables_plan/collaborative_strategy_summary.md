# SRD Builder: Collaborative Strategy Summary

**Date:** 2025-11-01
**Participants:** Human, GPT, Copilot, Claude
**Goal:** Align on equipment fixes + establish strategic patterns for future datasets

---

## The Challenge

Equipment extraction works but has bugs (AC parsing, weight format, missing fields). Meanwhile, you have 7 more datasets to extract (spells, lineages, classes, etc.).

**Tension:** Fix current bugs vs. design for future datasets?

**Solution:** Do both - fix bugs while extracting reusable patterns.

---

## Key Decisions

### 1. Schema Philosophy: Hybrid Approach

**Copilot's Position:** "Schema should match current reality exactly"
**Claude's Position:** "Schema should be future-ready for magic items"
**Resolution:** **Both** - Current fields + clearly marked future fields

**Concrete Example - Weight:**
```json
{
  "weight_lb": 10,        // Number for calculations (Claude's ask)
  "weight_raw": "10 lb."  // String preserving source (Copilot's ask)
}
```

**Result:** Consumers get both formats, magic items work seamlessly later

---

### 2. Implementation Strategy: Phased & Incremental

**Phase 1 (This Week):** Fix 5 equipment bugs
- Armor AC column detection
- Weight parsing (both formats)
- Versatile damage extraction
- Range extraction
- Armor category detection

**Phase 2 (Next Week):** Extract reusable patterns
- Context tracker (hierarchical state across pages)
- Extraction strategies (tables, prose, formatted text)
- Document patterns

**Phase 3 (Week After):** Validate with spells dataset
- Tests structured prose extraction
- Proves patterns are reusable
- High-value dataset for users

---

### 3. Next Dataset: Spells (Not Lineages or Classes)

**Why spells:**
- ✅ Different enough from tables to validate new patterns
- ✅ Large dataset (~300 items) for thorough testing
- ✅ Structured prose format establishes second extraction strategy
- ✅ High value for game content consumers

**Defer:** Classes (most complex), lineages (need subrace handling)

---

## Schema Compromise Details

### Approved Schema Structure (v1.1.0)

**Four tiers:**

**Tier 1: Core Fields (Always Present)**
- id, name, simple_name, category, source, page
- Required for ALL items

**Tier 2: Category-Specific Fields (Present When Relevant)**
- armor_class, damage, weapon_type (weapons)
- cost, weight_lb, weight_raw (most items)
- Properties, versatile_damage, range (some weapons)

**Tier 3: Future Fields (For Magic Items)**
- variant_of, is_magic, rarity, requires_attunement, modifiers
- Clearly marked with "FUTURE:" in description
- All null/false for base equipment

**Tier 4: Internal Metadata (Extraction Debugging)**
- section, table_header, row_index, _meta
- For builders, not consumers

### Key Compromise: Weight Format

**Old way:** Choose string OR number
**New way:** Emit both

```json
{
  "weight_lb": 10.5,       // For sorting, encumbrance calculations
  "weight_raw": "10.5 lb." // For exact source fidelity
}
```

**Parser change:**
```python
weight_lb, weight_raw = parse_weight("10 lb.")
item['weight_lb'] = weight_lb    # 10.0
item['weight_raw'] = weight_raw  # "10 lb."
```

### Key Compromise: Future Fields

**Old way (Copilot):** Don't include fields until extracted
**Old way (Claude):** Include all fields magic items will need
**New way:** Include optional fields with clear "FUTURE:" documentation

**Benefits:**
- Magic items use same schema (no v2.0 needed)
- Current data validates cleanly (all future fields null/false)
- Consumers know what's coming
- No confusion about missing data

---

## Extraction Patterns Identified

From equipment work, we've identified 5 reusable patterns:

### Pattern 1: Context Propagation
**Problem:** Section headers on page 62 affect tables on page 65
**Solution:** ContextTracker class maintains state across pages
**Used by:** All datasets (equipment, classes, lineages, spells)

### Pattern 2: Column Header Detection
**Problem:** Fixed column indices break across table variations
**Solution:** Parse header row to build dynamic column map
**Used by:** All table-based datasets

### Pattern 3: Multi-Strategy Extraction
**Problem:** Not all content is tables - need multiple approaches
**Solution:** Separate extractors for tables, structured prose, formatted text
**Used by:** Mixed datasets (classes = tables + prose)

### Pattern 4: Property Parsing
**Problem:** Complex data embedded in strings ("versatile (1d10)")
**Solution:** Regex extraction to structured fields
**Used by:** Weapons (versatile, range), potentially spells (components)

### Pattern 5: Flexible Schema Types
**Problem:** Same field appears as different types (weight as string vs number)
**Solution:** Emit multiple formats when needed (weight_lb + weight_raw)
**Used by:** Any field with calculation + display needs

---

## Implementation Priorities

### Must Fix (Phase 1 - This Week)
1. ✅ Armor AC parsing (CRITICAL - blocks validation)
2. ✅ Weight parsing (both formats)
3. ✅ Versatile damage extraction
4. ✅ Range extraction
5. ✅ Armor category detection

### Must Build (Phase 2 - Next Week)
1. ✅ ContextTracker class (reusable)
2. ✅ Extraction strategies module (reusable)
3. ✅ Documentation of patterns

### Must Validate (Phase 3 - Week After)
1. ✅ Spells extraction using patterns
2. ✅ Prove <20% new code for second dataset
3. ✅ Patterns documented and tested

---

## Success Metrics

### Equipment is "Done" when:
- [ ] All 114 items parse correctly
- [ ] AC values correct for armor (13, not 50)
- [ ] Weight in both formats (10.0 + "10 lb.")
- [ ] Versatile damage extracted ("1d10")
- [ ] Range extracted (20/60)
- [ ] Armor categories correct (light/medium/heavy)
- [ ] Schema validates 100%
- [ ] Test coverage >80%

### Patterns are "Proven" when:
- [ ] Second dataset (spells) implemented
- [ ] Uses extracted patterns (ContextTracker, extractors)
- [ ] Less than 20% new extraction code
- [ ] Patterns documented in EXTRACTION_PATTERNS.md

### Project is "On Track" when:
- [ ] Equipment + spells done in 3 weeks
- [ ] Clear path to lineages, classes, monsters
- [ ] Schema versioning strategy established
- [ ] Cross-references working (tables.json, magic items)

---

## Documents Created

1. **`srd_equipment_strategic_plan.md`** (27 pages)
   - Full analysis of bugs, patterns, and long-term vision
   - Cross-dataset architecture guidance
   - Schema design principles
   - Testing strategies

2. **`schema_compromise_recommendation.md`** (12 pages)
   - Detailed schema compromise explanation
   - Tier documentation strategy
   - Version strategy (1.1.0 → 1.2.0 → 2.0.0)
   - Alternative approaches

3. **`gpt_action_plan.md`** (18 pages)
   - Concrete implementation steps
   - Code examples for each fix
   - Test cases
   - File creation/update checklist

4. **This document** - Executive summary tying it all together

---

## How to Use These Documents

### For GPT (Implementation)
**Start with:** `gpt_action_plan.md`
- Follow Phase 1 implementation steps
- Use code examples provided
- Add tests as you go
- Reference strategic plan for "why"

### For Copilot (Review)
**Start with:** This summary + `schema_compromise_recommendation.md`
- Verify compromises address concerns
- Review Phase 1 changes for pragmatism
- Flag any issues early
- Approve schema before implementation

### For Human (Coordination)
**Start with:** This summary
- Use to align GPT and Copilot
- Reference strategic plan for decisions
- Track against success metrics
- Escalate blockers

---

## Next Steps (Immediate)

### Today:
1. ✅ Share these documents with GPT and Copilot
2. ✅ Align on schema compromise approach
3. ✅ Confirm Phase 1 implementation plan

### This Week:
1. GPT implements Phase 1 fixes
2. Copilot reviews each fix incrementally
3. Human validates equipment.json completeness
4. Update schema to v1.1.0

### Next Week:
1. Extract reusable patterns (Phase 2)
2. Document in EXTRACTION_PATTERNS.md
3. Begin spells extraction

---

## Questions to Resolve

Before starting implementation, confirm:

1. **Schema approach:** Approve hybrid schema (weight_lb + weight_raw, future fields marked)?
2. **Phase 1 scope:** All 5 bugs, or prioritize subset?
3. **Testing requirements:** Unit tests for each function, or integration tests only?
4. **Next dataset:** Spells confirmed, or prefer conditions/lineages?
5. **Code review process:** Per-fix review, or batch at end?

---

## Risk Mitigation

### Risk: Schema changes break consumers
**Mitigation:** Semantic versioning (1.1.0 = non-breaking, 2.0.0 = breaking)

### Risk: Pattern extraction takes longer than expected
**Mitigation:** Phase 2 is optional - can proceed to spells without it

### Risk: Spells extraction reveals pattern flaws
**Mitigation:** Expected! Iterate patterns based on second dataset

### Risk: GPT/Copilot remain misaligned
**Mitigation:** This document + clear phase boundaries + incremental review

---

## Alignment Summary

| Aspect | Copilot's Priority | Claude's Priority | Resolution |
|--------|-------------------|-------------------|------------|
| Schema philosophy | Match current data | Plan for future | Hybrid: both formats |
| Implementation order | Fix bugs first | Design patterns | Phased: fix then extract |
| Field inclusion | Only extracted fields | Include future fields | Future fields marked clearly |
| Next dataset | Defer planning | Choose strategically | Spells (validates patterns) |
| Testing | Practical coverage | Comprehensive tests | Fixture-based, >80% |

**Status:** ✅ Aligned on all major decisions

---

## Timeline

**Week 1 (Nov 1-8):** Equipment bug fixes + schema v1.1.0
**Week 2 (Nov 9-15):** Pattern extraction + documentation
**Week 3 (Nov 16-22):** Spells extraction
**Week 4 (Nov 23-29):** Conditions extraction (quick win)
**Week 5+:** Lineages → Classes → Magic Items → Monsters

**Milestone:** Equipment + Spells done by Nov 22 (3 weeks)

---

## Communication Protocol

**During Phase 1 (Bug Fixes):**
- GPT implements one fix at a time
- Copilot reviews after each fix
- Human approves before moving to next

**During Phase 2 (Pattern Extraction):**
- GPT refactors working code
- Copilot ensures no regressions
- Human reviews pattern documentation

**During Phase 3 (Spells):**
- GPT uses patterns from Phase 2
- Copilot flags when patterns don't fit
- Human decides: adapt pattern or special-case spells

---

## Success Indicators

**Good signs:**
- ✅ Each fix takes <2 hours
- ✅ Tests pass after each fix
- ✅ Schema validates equipment.json
- ✅ Copilot approves changes quickly
- ✅ Pattern code is <200 lines

**Warning signs:**
- ⚠️ Fixes taking much longer than estimated
- ⚠️ Lots of edge cases not in original bugs
- ⚠️ Schema validation keeps failing
- ⚠️ Disagreement on approach after starting
- ⚠️ Pattern abstraction getting too complex

**Stop and reassess if:**
- 🛑 Phase 1 takes >2 weeks
- 🛑 More than 10 bugs discovered
- 🛑 Schema requires major restructure
- 🛑 Copilot rejects multiple fixes

---

## Conclusion

**Core Strategy:** Fix equipment bugs this week while laying foundation for future datasets.

**Key Innovation:** Hybrid schema approach satisfies both "current reality" and "future-ready" needs.

**Next Action:** Get GPT started on Phase 1, Fix #1 (Armor AC parsing).

**Expected Outcome:** Working equipment.json + proven patterns + clear path to 7 more datasets.

---

**Status:** Ready for implementation ✅
