# Parking Lot - Deferred Features

This document tracks features that have been discussed but deferred for later implementation.

---

## terminology.aliases Field in meta.json

**Status:** Deferred until second ruleset or naming conflict

### Intent
Help consumers find content when terminology differs between rulesets or versions. Provides a mapping from alternative terms to the canonical names used in this dataset.

### Example from Blackmoor
```json
"terminology": {
  "aliases": {
    "races": "lineages",
    "race": "lineage"
  },
  "note": "We use 'lineage' terminology to be future-proof and align with modern D&D direction."
}
```

### Context
- **Historical:** Originally `races/` directories were planned (README_v1.md)
- **Evolution:** Changed to `lineages.json` for future-proofing (README_v2.md)
- **Rationale:** Different game systems or SRD versions might use different terminology
- **Example:** D&D 5e uses "race", but newer editions might prefer "lineage" or "ancestry"

### Open Questions

1. **Scope:** Is this for top-level file names only, or also field names within data structures?
   - Example: Should it map `monster.race` → `monster.lineage`?
   - Or just `races.json` → `lineages.json`?

2. **Direction:** Which way should the mapping go?
   - Option A: Old → New (`races` → `lineages`) - "if you're looking for races, check lineages"
   - Option B: New → Old (`lineages` → `races`) - "we call it lineages, you might know it as races"
   - Blackmoor uses Option A

3. **Per-Ruleset vs Global:**
   - Should each ruleset have its own aliases?
   - Or should this be a global srd-builder convention?
   - SRD 5.1 specifically uses "classes" and "races" terminology in the source PDF
   - Other systems might differ

4. **When to Add:**
   - Add now as empty placeholder?
   - Add when we extract a second ruleset with different terminology?
   - Add when we actually encounter a naming conflict?

5. **Consumer Behavior:**
   - How should consumers use this? Auto-redirects? Documentation only?
   - Should we provide utility functions to resolve aliases?

### Decision Point
Implement when:
- We extract a second ruleset with different terminology, OR
- We identify an actual naming conflict that affects consumers, OR
- A consumer specifically requests this feature

### Related Files
- `docs/external/blackmoor/README_v1.md` - Original structure with `races/`
- `docs/external/blackmoor/README_v2.md` - Updated structure with `lineages.json`
- `docs/external/blackmoor/meta.json` - Reference implementation with aliases

### Implementation Checklist (When Triggered)
- [ ] Decide on alias direction and scope
- [ ] Update `_generate_meta_json()` in `build.py`
- [ ] Add schema validation for terminology section
- [ ] Document usage in README
- [ ] Consider adding to TEMPLATE files
- [ ] Update tests to verify alias structure

---

## Item Variants & Magic Items Architecture

**Date Raised:** 2025-10-30
**Status:** Research needed
**Priority:** Medium (affects future magic item extraction)

### The Question

How should we represent item variants and magic items in relation to base equipment?

**Scenarios:**
- Base items: Longsword, Chain Mail (mundane equipment from SRD Chapter 5)
- Quality variants: Old rusty longsword, Masterwork chain mail
- Magic items: +1 Longsword, Sword of Sharpness, Armor of Invulnerability
- Named items: Sword of Office (unique, but fundamentally a longsword)

### Architecture Options

#### Option 1: Single Unified Schema
All items (mundane + magic) in one schema with optional fields.

**Pros:**
- Simple for consumers (one place to look)
- No reference resolution needed
- Easy queries (all longswords in one list)

**Cons:**
- Large files (mixing mundane + magic)
- Many optional fields
- Harder to maintain (SRD vs DMG content mixed)

#### Option 2: Separate Files with References
- `equipment.json` - base mundane items (SRD Chapter 5)
- `magic_items.json` - magic variants with `base_item_id` references (DMG Chapter 7)

**Pros:**
- Clean extraction boundaries (matches source documents)
- Smaller files, focused content
- Consumers compose as needed
- Both use `item:*` namespace

**Cons:**
- Consumers must resolve references
- More complex queries (need to join)
- Need clear composition rules

#### Option 3: Composition Pattern
Items can reference other items as templates with overrides.

**Pros:**
- Flexible inheritance model
- Supports variants, quality levels, customization
- DRY (don't repeat base stats)

**Cons:**
- Complex resolution logic
- Deep nesting possible
- Performance concerns for consumers

### Alignment with Terminology Guidance

Following the **filename vs namespace** pattern from terminology.aliases.md:
- **Filename** = Source document structure (helps humans find content)
- **Namespace** = Game engine data type (helps code reference content)

**Proposed:**
- `equipment.json` - mundane items from SRD Chapter 5 (current v0.5.0 work)
- `magic_items.json` - magic items from DMG Chapter 7 (future)
- Both use `item:*` namespace
- Magic items can include `base_item_id: "item:longsword"` to reference base

### Questions for Research

1. **Schema flexibility:** Should base equipment schema include optional magic fields now, or add later?
2. **Reference pattern:** How do consumers efficiently resolve `base_item_id` references?
3. **Inheritance rules:** What fields can be overridden vs inherited from base?
4. **Unique items:** Do artifacts/named items need base references, or standalone?
5. **Quality variants:** How to represent rusty/masterwork/silvered as separate from magic?
6. **Multiple rulesets:** How does this pattern scale across SRD, DMG, homebrew?

### Next Steps

- [ ] Research how other TTRPGs/systems handle item variants (D&D Beyond, Foundry VTT, etc.)
- [ ] Collaborate with GPT on composition patterns and consumer UX
- [ ] Prototype magic item schema with reference pattern
- [ ] Test consumer queries with joined data
- [ ] Document composition rules and examples

### Related Files
- `schemas/equipment.schema.json` - Current base item schema
- `docs/templates/TEMPLATE_equipment.json` - Current template
- `docs/terminology.aliases.md` - Filename/namespace pattern guidance

---

## Blackmoor Integration Feedback

**Date Raised:** 2025-11-01 (review of v0.4.2, updated with v0.5.0)
**Status:** Active development priority
**Source:** Primary consumer and reason for srd-builder existence

### Context

Blackmoor reviewed srd-builder v0.4.2 package and provided comprehensive feedback. They are building a VTT (Virtual Tabletop) engine with combat formulas that need structured monster/equipment data.

**What They Love ✅**
- Schema v1.1.0: "well-executed and production-ready"
- Documentation: SCHEMAS.md and DATA_DICTIONARY.md are "fantastic"
- Namespacing (monster:, item:): "perfect"
- simple_name field: "excellent for indexing"
- Version tracking in _meta: "exactly what's needed"
- Structured data (armor_class, hit_points as objects)
- Note: We already support by_cr and by_type indexes in indexer.py

### High Priority - Action Data Parsing

**Current State:**
Actions have inconsistent parsing - some have structured fields, some don't.

**Example of good parsing:**
```json
{
  "name": "Tentacle",
  "simple_name": "tentacle",
  "damage_type": "bludgeoning",  // ✅ Good!
  "damage_dice": "2d6 + 5",       // ✅ Good!
  "to_hit": 9,                    // ✅ Good!
  "reach": 10,                    // ✅ Good!
  "text": "..."                   // ✅ Still have raw text
}
```

**Request:**
For ALL Melee Weapon Attack and Ranged Weapon Attack actions, parse:
- `to_hit` (integer)
- `reach` or `range` (integer or object)
- `damage_dice` (string like "2d6+5")
- `damage_type` (string)

**Why:** Blackmoor's combat formulas (`resolve_5e_melee_attack`) need direct access to this data without text parsing.

**Implementation Notes:**
- Improve parsing in parse_monsters.py action processing
- Ensure consistency across all 296 monsters
- Keep raw `text` field for fallback
- Add test coverage for action field extraction

---

### Medium Priority - Saving Throw Parsing

**Current State:**
```json
"saving_throw": "DC 14 Constitution"  // String
```

**Request:**
```json
{
  "saving_throw": {
    "dc": 14,
    "ability": "constitution",
    "on_save": "half",  // or "none", "half_damage", etc.
    "raw": "DC 14 Constitution"
  }
}
```

**Why:** Enables automated saving throw resolution in combat engine.

**Implementation Notes:**
- Parse common patterns: "DC X [Ability]", "DC X [Ability] saving throw"
- Extract on_save behavior from action text (half damage, negates, etc.)
- Keep raw field for edge cases
- Update monster.schema.json to support both formats during transition

---

### Low Priority - Ability Score Modifiers

**Current State:**
Only raw ability scores provided.

**Request:**
```json
{
  "ability_scores": {
    "strength": 21,
    "strength_modifier": 5  // Auto-calculated: (21 - 10) / 2
  }
}
```

**Why:** Common lookup, saves calculation on every use.

**Implementation Notes:**
- Add in postprocess.py normalization
- Formula: (score - 10) // 2
- Consider adding to all ability scores or just when needed
- Balance: convenience vs data bloat

---

### Equipment Properties (Future)

**Current Status:** Equipment v0.5.0 has 111 items, noted as "still in dev"

**Request:** Once stable, add properties parsing for weapons as structured array:
```json
{
  "properties": ["versatile", "finesse", "two-handed"]
}
```

**Why:** Currently properties are in text descriptions, need structured data for rule automation.

**Defer Until:** Equipment schema stabilizes.

---

### Additional Suggestions

1. **build_report.json enhancements** - Add extraction warnings/issues encountered
2. **Spells (Future)** - High priority for Blackmoor since prompts reference spell mechanics
3. **Damage Resistance/Immunity** - Current structure with {type, qualifier} is "perfect, keep it"

---

### Implementation Priority

**v0.6.0 or v0.7.0:**
1. Action data consistency (HIGH - blocks combat integration)
2. Saving throw parsing (MEDIUM - needed for full combat)
3. Ability score modifiers (LOW - nice to have)

**Future:**
4. Equipment properties (defer until schema stable)
5. Spells extraction (separate milestone)

---

### Related Files
- `src/srd_builder/parse_monsters.py` - Action parsing logic
- `src/srd_builder/postprocess.py` - Normalization and computed fields
- `src/srd_builder/indexer.py` - Already has by_cr, by_type support ✅
- `docs/external/blackmoor/blackmoor_srd_5_1_package review.md` - Full review

---

## [Add more parked features here as needed]
