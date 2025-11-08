# Parking Lot - Deferred Features

This document tracks features that have been discussed but deferred for later implementation.

---

## **v0.8.2 Classes - Table Extraction** ✅ COMPLETE

**Status:** All 12 class progression tables extracted and integrated!

**Extracted Tables (pages 8-55):**
- ✅ `table:barbarian_progression` - Rage damage, rages per day, class features by level
- ✅ `table:bard_progression` - Cantrips known, spells known, spell slots, bardic inspiration die
- ✅ `table:cleric_progression` - Cantrips known, spell slots by level, channel divinity uses
- ✅ `table:druid_progression` - Cantrips known, spell slots, wild shape limits
- ✅ `table:fighter_progression` - Class features, extra attacks by level
- ✅ `table:monk_progression` - Martial arts die, ki points, unarmored movement
- ✅ `table:paladin_progression` - Spell slots (half caster), divine smite dice
- ✅ `table:ranger_progression` - Spell slots (half caster), favored enemies
- ✅ `table:rogue_progression` - Sneak attack dice, class features
- ✅ `table:sorcerer_progression` - Cantrips known, spells known, spell slots, sorcery points
- ✅ `table:warlock_progression` - Cantrips known, spells known, spell slots (pact magic), invocations
- ✅ `table:wizard_progression` - Cantrips known, spell slots

**Implementation:**
- Added 12 table targets to `scripts/table_targets.py`
- Added 12 manual extraction methods to `src/srd_builder/extract_tables.py`
- Each table has 20 rows (levels 1-20) with class-specific columns
- Total: 23 tables in tables.json (12 class progression + 11 reference tables)
- All tests pass (113 tests)

**References:**
- Table targets: `scripts/table_targets.py`
- Extraction logic: `src/srd_builder/extract_tables.py`
- Class data: `src/srd_builder/class_targets.py`
- Parse logic: `src/srd_builder/parse_classes.py` (includes table references)
- Schema: `schemas/class.schema.json`

---

## Data Parsing Gaps - RESOLVED IN v0.6.4 ✅

**Status:** All critical spell parsing gaps FIXED in v0.6.4
**Priority:** ~~HIGH~~ → COMPLETE

### Spell Parsing Gaps

**v0.6.3 Status:**
- ✅ 319/319 spells extracted (100%)
- ✅ Text quality: 0 spells with <50 chars
- ⚠️ Effects coverage: 44% (140/319)
- ❌ Ritual flag: 0% - **BROKEN**
- ❌ Area-of-effect: 0%
- ❌ Healing effects: 0%
- ❌ Attack roll effects: 0%

**v0.6.4 Status:**
- ✅ 319/319 spells extracted (100%)
- ✅ Text quality: 0 spells with <50 chars
- ✅ Effects coverage: 52% (166/319) - **+8 percentage points**
- ✅ Ritual flag: 100% (29/319) - **COMPLETE** (manually verified v0.8.2)
- ✅ Area-of-effect: 17% (55/319) - **NEW** (Fireball, Burning Hands, Lightning Bolt)
- ✅ Healing effects: 2% (5/319) - **NEW** (Cure Wounds, Healing Word)
- ✅ Attack roll effects: 6% (19/319) - **NEW** (Fire Bolt, Shocking Grasp)

#### 1. Ritual Flag Extraction (FIXED ✅)
**Impact:** 29 spells now correctly flagged as ritual
**Root Cause:** Raw data had "(ritual)" in `level_and_school` field, not `casting_time`
**Fix Applied:** Check `level_and_school` field for "(ritual)" marker
**Examples:** Detect Magic, Identify, Find Familiar, Alarm, Commune
**Commit:** 3049c70

#### 2. Area-of-Effect Parsing (IMPLEMENTED ✅)
**Impact:** 55 spells now have structured area data (17%)
**Fix Applied:**
- Regex pattern handles PDF spacing: `(\d+)-?\s*foot[-\s]*(radius[-\s]*)?(sphere|cone|cube|cylinder)`
- Line spells: `(\d+)\s+feet\s+long(?:\s+and\s+(\d+)\s+feet\s+wide)?`
- Extracts to `effects.area: {shape, size, unit}`
**Examples:** Fireball (20-foot sphere), Burning Hands (15-foot cone), Lightning Bolt (100-foot line)
**Commit:** 3049c70

#### 3. Healing Effects (IMPLEMENTED ✅)
**Impact:** 5 spells have dice-based healing data (2%)
**Fix Applied:** Parse "regains hit points equal to XdX" pattern
**Schema Note:** Fixed-amount healing (Heal, Mass Heal) excluded - schema requires dice pattern
**Examples:** Cure Wounds (1d8), Healing Word (1d4), Mass Cure Wounds (3d8), Prayer of Healing (2d8)
**Commit:** 37927ae

#### 4. Attack Roll Effects (IMPLEMENTED ✅)
**Impact:** 19 spells have attack type data (6%)
**Fix Applied:** Parse "make a (melee|ranged) spell attack" pattern
**Schema-compliant types:** `melee_spell`, `ranged_spell`
**Examples:** Fire Bolt, Chill Touch (ranged), Shocking Grasp, Contagion (melee)
**Commit:** 37927ae

### Equipment Parsing Gaps

**Current Status (v0.6.4):**
- ✅ 106 items (deduplicated from 111)
- ✅ 68 "gear" items (adventuring gear as subcategory/property)
- ⚠️ 8/13 containers have capacity
- ✅ Category "gear" is correct primary category

#### 1. Adventuring Gear Category Label (CLARIFIED ✅)
**Status:** RESOLVED - "gear" is correct primary category
**Investigation:** equipment.schema.json enum includes "gear" as valid category
**Verification:** All equipment tests pass (test_parse_equipment.py, test_golden_equipment.py)
**Design Note:** "adventuring_gear" would be a subcategory, property, or terminology alias if needed for discoverability, but "gear" is the correct primary category value#### 2. Container Capacity Gaps (documented separately below)
See "Container Capacity Hardcoded Values" section.

### Monster Parsing Gaps

**Current Status (v0.6.3):**
- ✅ 296 monsters extracted
- ✅ 244/296 (82%) have traits (special abilities)
- ✅ 293/296 (99%) have actions
- ✅ 30 legendary creatures
- ✅ 8 with reactions
- ✅ Query error showed "special_abilities: 0" but field is actually "traits"

#### Status: No Critical Gaps! ✅
Monster parsing is in excellent shape. Field is `traits` not `special_abilities` - documentation/query error only.

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

**Note on Index Features:**
Blackmoor's review requested `by_cr` and `by_type` indexes be added. However, these have been present in index.json since the indexer was first created (commit 7a1b633, before v0.4.2). The review may have been based on documentation rather than examining the actual generated index.json file. The "Gap" they identified in section B was actually about **their own code** lacking utility functions to consume the index, not missing features in srd-builder.

### ✅ Action Data Parsing - IMPLEMENTED (v1.2.0)

**Status:** COMPLETE

**Previous State:**
Actions had inconsistent parsing - some had structured fields, some didn't.

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

**Delivered:**
- 472/884 total action entries (53.4%) with structured combat data
- Fields: attack_type, to_hit, reach/range, damage, saving_throw
- Preserves original text field for fallback
- 14 comprehensive tests (all passing)
- Applies to actions, legendary_actions, and reactions

**Implementation:**
- New parse_actions.py module with regex-based extraction
- Integrated into postprocess.py pipeline
- Example: Aboleth Tentacle has attack_type, to_hit, reach, damage, damage_options, saving_throw

**Why:** Enables Blackmoor's combat formulas (`resolve_5e_melee_attack`) to access data without text parsing.

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

### ✅ Ability Score Modifiers - IMPLEMENTED

**Status:** COMPLETE (v0.5.0+)

**Implementation:**
```json
{
  "ability_scores": {
    "strength": 21,
    "strength_modifier": 5,
    "dexterity": 10,
    "dexterity_modifier": 0,
    ...
  }
}
```

**Delivered:**
- Added `add_ability_modifiers()` to postprocess.py
- Formula: (score - 10) // 2
- Integrated into clean_monster_record() pipeline
- 5 comprehensive tests (all passing)

**Benefits:** No runtime calculation needed, common lookup optimized

---

### Equipment Properties Normalization

**Current Status:** Equipment v0.5.0 has 111 items

**Current State:**
```json
{
  "properties": ["versatile (1d10)", "thrown (range 20/60)"]
}
```

**Request:** Remove embedded data from properties array:
```json
{
  "properties": ["versatile", "thrown"]
}
```

**Rationale:**
- `versatile_damage` and `range` are already parsed as separate fields
- Properties array duplicates data
- Cleaner for rule automation (check for "versatile" without parsing parens)

**Implementation Notes:**
- Strip parenthetical data from properties during equipment parsing
- Verify versatile_damage and range fields capture all the data
- Update equipment tests to reflect clean properties
- Consider adding to clean_equipment_record() in postprocess.py

**Priority:** LOW - nice-to-have, non-blocking (Blackmoor's integration already complete)

---

### Additional Suggestions

1. **build_report.json enhancements** - Add extraction warnings/issues encountered
2. **Spells (Future)** - High priority for Blackmoor since prompts reference spell mechanics
3. **Damage Resistance/Immunity** - Current structure with {type, qualifier} is "perfect, keep it"

---

### Implementation Status

**✅ COMPLETED (v1.2.0):**
- Ability score modifiers
- Action data parsing (472/884 actions with structured fields)

**Blackmoor Integration Status (as of 2025-11-01):**
- ✅ Full SRD v0.5.0 integration (296 monsters, 111 equipment)
- ✅ Data loader with caching
- ✅ REST API endpoints
- ✅ Equipment helpers for combat
- ✅ All tests passing
- 🎉 **Integration complete and working!**

**Next Priorities (from Blackmoor 2025-11-01):**

1. **Spells** (HIGH - v0.6.0 target)
   - D&D gameplay is spell-heavy for casters
   - Complements monsters (many have spellcasting) and equipment
   - Critical for character actions in combat/narrative
   - Schema proposal: docs/external/blackmoor/spell_schema_proposal.md
   - Estimated ~300-400 spells in SRD 5.1

2. **Conditions** (MEDIUM - quick win)
   - Referenced constantly (poisoned, stunned, charmed, etc.)
   - Needed for monster abilities and spell effects
   - Small dataset (~15-20 conditions)
   - Simple schema: {id, name, simple_name, text, mechanics}

3. **Equipment Properties Normalization** (LOW)
   - Remove embedded data from properties array
   - Current: ["versatile (1d10)"] → Target: ["versatile"]
   - Non-blocking (Blackmoor integration already complete)

4. **Saving Throw Parsing** (MEDIUM - deferred)
   - Would enable automated saving throw resolution
   - Change from string to object (MAJOR version bump required)
   - Current: "DC 14 Constitution" → Target: {dc: 14, ability: "constitution", on_save: "half"}

5. **Classes & Lineages/Races** (LOWER priority)
   - More complex extraction (multi-page, tables, progression)
   - Character creation features
   - Can defer until character sheet features needed

---

### Related Files
- `src/srd_builder/parse_monsters.py` - Action parsing logic
- `src/srd_builder/postprocess.py` - Normalization and computed fields
- `src/srd_builder/indexer.py` - Already has by_cr, by_type support ✅
- `docs/external/blackmoor/blackmoor_srd_5_1_package review.md` - Full review

---

## Container Capacity Hardcoded Values

**Date Raised:** 2025-11-02
**Status:** Technical debt - works but not ideal
**Priority:** MEDIUM - will bite us when we improve table extraction

### Context

The Container Capacity table (SRD pages 69-70) lists 13 containers with their capacities. PDF table extraction only captured 5/13 entries due to multi-column layout complexity.

**Currently Hardcoded (parse_equipment.py):**
```python
CONTAINER_CAPACITIES = {
    "backpack": "1 cubic foot/30 pounds of gear",
    "barrel": "40 gallons liquid, 4 cubic feet solid",
    "basket": "2 cubic feet/40 pounds of gear",
    "bottle_glass": "1½ pints liquid",
    "bucket": "3 gallons liquid, 1/2 cubic foot solid",
    "chest": "12 cubic feet/300 pounds of gear",
    "flask_or_tankard": "1 pint liquid",
    "jug_or_pitcher": "1 gallon liquid",
    "pot_iron": "1 gallon liquid",
    "pouch": "1/5 cubic foot/6 pounds of gear",
    "sack": "1 cubic foot/30 pounds of gear",
    "vial": "4 ounces liquid",
    "waterskin": "4 pints liquid",
}
```

### The Problem

**Extracted via PDF:** 5/13 (Basket, Bucket, Flask, Pot, Waterskin)
**Missing from extraction:** 8/13 (Backpack, Barrel, Bottle, Chest, Jug, Pouch, Sack, Vial)

**Root Cause:** The Container Capacity table spans pages 69-70 in a multi-column layout. Current table extraction logic struggles with:
- Split tables across pages
- Multi-column tables that continue mid-page
- Table headers that don't align with all columns

### Current Solution (v0.6.2+)

Applied hardcoded capacity values to all 13 containers in equipment parsing:
- ✅ All 13 containers now have `capacity` field
- ✅ Added `container: true` property for filtering
- ✅ Works correctly for consumers
- ⚠️ Will break if container names change in future SRDs
- ⚠️ Hardcoded values may drift from source if SRD updates

### Why This Will Bite Us

1. **Future SRDs:** New containers or capacity changes won't be detected
2. **Table Extraction Improvements:** When we fix multi-column extraction, we'll need to:
   - Remove hardcoded values
   - Test that extraction captures all 13 containers
   - Ensure no regressions
3. **Maintenance:** Easy to forget this is hardcoded, values could drift
4. **Other Tables:** Other multi-column/split tables may need similar workarounds

### Proper Solution (Future)

**Phase 1: Improve Table Extraction**
- Detect multi-column table layouts
- Track table continuation across pages
- Merge split rows correctly
- Handle column headers that span multiple data columns

**Phase 2: Remove Hardcoding**
- Delete CONTAINER_CAPACITIES dict
- Verify extraction captures all 13 containers
- Add test to ensure no hardcoded fallbacks exist

**Phase 3: Validation**
- Compare extracted values against known-good reference
- Flag mismatches as warnings
- Use reference data for validation, not as fallback

### Related Issues

This is part of a larger pattern:
- Equipment extraction struggles with complex PDF tables
- Multi-column layouts confuse row association
- Page breaks mid-table lose context
- Headers don't always align with data columns

**Other affected tables:**
- Armor table (pages 65-66) - multiple columns, subcategories
- Weapon table (pages 66-68) - properties split across columns
- Tool table (pages 70-71) - tools + artisan's tools

### Implementation Checklist (When Fixing)

- [ ] Research multi-column table detection algorithms
- [ ] Implement column boundary detection
- [ ] Handle table continuation across pages
- [ ] Test on Container Capacity table (should get 13/13)
- [ ] Remove CONTAINER_CAPACITIES hardcoded dict
- [ ] Add integration test comparing extracted vs reference data
- [ ] Document table extraction improvements in CHANGELOG

### Files Affected

- `src/srd_builder/parse_equipment.py` - Contains CONTAINER_CAPACITIES dict
- `src/srd_builder/extract_equipment.py` - Table extraction logic
- `tests/test_parse_equipment.py` - Should verify container capacities

### Notes

**Current approach is pragmatic:** Get the data into the right structure now, improve extraction later. This unblocks consumers (Blackmoor) who need container capacities for inventory management.

**Do NOT remove this note** until table extraction properly captures all 13 containers without hardcoded fallbacks.

---

## Equipment Name Aliases

**Date Raised:** 2025-11-02
**Status:** Identified, deferred
**Priority:** MEDIUM (UX improvement)
**Related:** See "terminology.aliases Field in meta.json" above - same pattern applies

### The Problem

Some equipment items have compound names that hurt searchability:
- **"Flask or tankard"** - searching for "tankard" alone won't find this
- **"Jug or pitcher"** - searching for "pitcher" alone won't find this

This is the same issue as terminology aliases (conditions, game terms) but for equipment names.

### Proposed Solution

Apply the same alias pattern as terminology - add `aliases` array to equipment items:

```json
{
  "id": "item:flask_or_tankard",
  "name": "Flask or tankard",
  "simple_name": "flask_or_tankard",
  "aliases": ["flask", "tankard"],
  "capacity": "1 pint liquid",
  "container": true,
  "cost": {
    "value": 2,
    "unit": "cp"
  }
}
```

With index enhancement:
```json
{
  "equipment": {
    "by_name": {
      "flask or tankard": "item:flask_or_tankard",
      "flask": "item:flask_or_tankard",
      "tankard": "item:flask_or_tankard",
      "jug or pitcher": "item:jug_or_pitcher",
      "jug": "item:jug_or_pitcher",
      "pitcher": "item:jug_or_pitcher"
    }
  }
}
```

### Implementation Phases

1. **Schema Update:**
   - Add optional `aliases: string[]` to equipment.schema.json
   - Document field in SCHEMAS.md

2. **Parser Enhancement:**
   - Add aliases to compound-named items in parse_equipment.py
   - Initially just "Flask or tankard" and "Jug or pitcher"

3. **Indexer Update:**
   - Modify indexer.py to expand by_name with alias entries
   - Each alias becomes a separate lookup key pointing to same ID

4. **Testing:**
   - Verify search/lookup works for component names
   - Test that "tankard" → "item:flask_or_tankard"
   - Test that "pitcher" → "item:jug_or_pitcher"

5. **Documentation:**
   - Document alias pattern in SCHEMAS.md
   - Consider unified alias docs with terminology aliases

### When This Will Bite Us

- **Search UI:** When consumers build search/filter and users can't find "tankard"
- **Inventory Systems:** When matching item references from adventures/modules
- **Cross-referencing:** When other sources reference "pitcher" but we only have "jug or pitcher"
- **AI/LLM queries:** When players ask "do I have a tankard?" and system can't find it

### Future Considerations

Should this pattern extend to other compound/quantity names?
- **"Arrows (20)"** - alias "arrow" or "arrows"?
- **"Caltrops (bag of 20)"** - alias "caltrop" or "caltrops"?
- **"Ball bearings (bag of 1,000)"** - alias "ball bearing"?

May need quantity-aware alias handling if we expand beyond simple compound names.

### Alignment with Terminology Pattern

Both equipment aliases and terminology aliases solve the same UX problem:
- **Core issue:** Multiple valid names for the same concept
- **Solution:** Store all valid names, map to canonical ID
- **Schema pattern:** Optional `aliases` array on entities
- **Index pattern:** Expand lookup keys to include aliases
- **Consumer benefit:** Flexible search without guessing exact name

Consider implementing both together for consistency.

### Implementation Checklist (When Triggered)

- [ ] Add `aliases` field to equipment.schema.json
- [ ] Add aliases to "Flask or tankard" and "Jug or pitcher"
- [ ] Update indexer to expand by_name with aliases
- [ ] Add tests for alias lookup
- [ ] Document alias pattern in SCHEMAS.md
- [ ] Consider unified alias documentation with terminology
- [ ] Evaluate other compound-named items for aliases

---

## Code Complexity Technical Debt

**Date Raised:** 2025-11-02
**Status:** Technical debt - bypassed with noqa comments
**Priority:** MEDIUM - should address before complexity becomes unmaintainable

### The Problem

Several parsing functions exceed Ruff's complexity limit (C901, max 10) and have been suppressed with `# noqa: C901` comments:

1. **parse_equipment.py: `parse_equipment_records()`** - Complexity 11
   - Handles deduplication logic for duplicate table entries
   - Merges capacity data from Container Capacity table
   - Applies hardcoded CONTAINER_CAPACITIES fallback

2. **parse_spells.py: `parse_spell_records()`** - Complexity 11
   - Parses spell headers (casting time, range, components, duration)
   - Fixes edge case for multi-page spells
   - Extracts effects and scaling from description

3. **validate.py: `check_data_quality()`** - Complexity 13
   - Checks for empty spell text
   - Checks for duplicate IDs across multiple index sections
   - Nested loops for validating index structure

### Why This Is Technical Debt

- **Maintainability:** Complex functions are harder to understand and modify
- **Testing:** Large functions are harder to test comprehensively
- **Bugs:** Higher complexity correlates with higher bug rates
- **Code review:** Reviewers struggle with complex functions
- **Suppressions mask the problem:** `# noqa` comments don't fix the underlying issue

### Proper Solution

**Refactoring Strategy:**

1. **Extract helper functions** - Break complex logic into smaller, focused functions
   - `parse_equipment_records()`: Extract deduplication logic, capacity merging
   - `parse_spell_records()`: Extract header parsing, effect extraction
   - `check_data_quality()`: Extract per-check functions

2. **Use early returns** - Reduce nesting depth with guard clauses

3. **Data-driven approaches** - Replace conditionals with lookup tables where appropriate

4. **Measure improvement** - Run complexity analysis before/after refactoring

### Implementation Phases

**Phase 1: parse_equipment_records() (Priority: HIGH - blocks hardcoded capacity fix)**
- [ ] Extract `_deduplicate_items()` function
- [ ] Extract `_merge_capacity_data()` function
- [ ] Extract `_apply_hardcoded_capacities()` function
- [ ] Reduce main function to orchestration only
- [ ] Target complexity: ≤ 8

**Phase 2: parse_spell_records() (Priority: MEDIUM)**
- [ ] Extract `_parse_spell_header()` function (casting, range, components, duration)
- [ ] Extract `_fix_multipage_spell_text()` function
- [ ] Extract effect/scaling extraction into separate module
- [ ] Target complexity: ≤ 8

**Phase 3: check_data_quality() (Priority: MEDIUM)**
- [ ] Extract `_check_empty_spell_text()` function
- [ ] Extract `_check_index_duplicates()` function
- [ ] Make extensible for adding new checks
- [ ] Target complexity: ≤ 6

**Phase 4: Establish Complexity Guidelines**
- [ ] Document complexity limits in CONTRIBUTING.md
- [ ] Add complexity reporting to CI
- [ ] Require complexity justification in PR reviews for functions > 8

### When This Will Bite Us

- When adding new parsing logic (equipment variants, magic items)
- When debugging extraction issues (hard to trace through complex functions)
- When onboarding new contributors (steep learning curve)
- When refactoring table extraction (tightly coupled with parsing)

### Related Technical Debt

- Container capacity hardcoding (see above) - tied to equipment parser complexity
- Table extraction improvements - will add more complexity without refactoring
- Multiple ruleset support - will multiply complexity if not addressed

### Success Metrics

- All `# noqa: C901` comments removed
- All functions ≤ 10 complexity (ideally ≤ 8)
- Improved test coverage of extracted functions
- Faster PR review times for parsing changes

---

## Ruff Configuration Migration

**Date Raised:** 2025-11-02
**Status:** Technical debt - deprecated configuration format
**Priority:** LOW - cosmetic warning, no functional impact

### The Problem

Ruff displays deprecation warning on every run:

```
warning: The top-level linter settings are deprecated in favour of their counterparts in the `lint` section. Please update the following options in `pyproject.toml`:
  - 'ignore' -> 'lint.ignore'
  - 'select' -> 'lint.select'
```

Current `pyproject.toml` uses old configuration format (top-level settings). Ruff now recommends nesting linter settings under `[tool.ruff.lint]` section.

### Impact

- **Functional:** None - old format still works, just deprecated
- **UX:** Warning noise on every lint/format run
- **Future:** May break in future Ruff versions when old format is removed

### Solution

Update `pyproject.toml` to use new configuration format:

**Before:**
```toml
[tool.ruff]
ignore = ["E501", ...]
select = ["E", "F", ...]
```

**After:**
```toml
[tool.ruff.lint]
ignore = ["E501", ...]
select = ["E", "F", ...]
```

### Implementation

- [ ] Move `ignore` setting from `[tool.ruff]` to `[tool.ruff.lint]`
- [ ] Move `select` setting from `[tool.ruff]` to `[tool.ruff.lint]`
- [ ] Check for other top-level linter settings that should move
- [ ] Test that linting behavior is unchanged
- [ ] Verify warning disappears

### Related

- Ruff configuration docs: https://docs.astral.sh/ruff/configuration/
- Should be done alongside other config updates (complexity thresholds, etc.)

---

## JSON Field Ordering & Consistency (v0.8.1+)

**Priority:** LOW (quality-of-life improvement)
**Effort:** Medium

### Problem

JSON output files have inconsistent field ordering:
- **Data files** (`monsters.json`, `equipment.json`, etc.): `_meta` wrapper with `ruleset`, `schema_version`, `source` first (good order)
- **meta.json**: Was `version`, `source` initially - changed to `source`, `ruleset_version` in v0.8.1
- Python dicts don't guarantee order in JSON output (though `OrderedDict` used in some places)
- No consistent policy on field ordering across the codebase

### Current Issues

1. **Field naming inconsistency:**
   - Initially used `version` in `meta.json` (ambiguous - builder version? ruleset version?)
   - Changed to `ruleset_version` for clarity
   - May have other fields with unclear names

2. **Ordering preferences:**
   - Identification fields (`source`, `ruleset`, `id`) should come first
   - Metadata/build info should come after core data
   - User expressed preference for: `source` → `ruleset_version` → `license` → `build` → rest

3. **No enforcement:**
   - Field order depends on dict insertion order
   - `json.dumps()` doesn't sort by default
   - `OrderedDict` used inconsistently

### Proposed Solution

**Phase 1: Document Standards**
- Create `docs/JSON_STYLE_GUIDE.md` with field ordering rules:
  - Core identification first (source, id, name, type)
  - Functional data second (stats, attributes, values)
  - Metadata last (pages, timestamps, build info)
- Add to ARCHITECTURE.md under design decisions

**Phase 2: Semantic Entity Keys (Breaking Change)**
- **Current:** All data files use generic `"items"` wrapper: `{"_meta": {...}, "items": [...]}`
- **Proposed:** Use entity-specific keys for clarity: `{"_meta": {...}, "monsters": [...]}`
- **Benefits:**
  - Self-documenting (no need to check filename or _meta to know content type)
  - Type-safe for consumers (TypeScript/JSON Schema benefits)
  - Matches index.json structure (already uses `"monsters"`, `"spells"`, `"classes"`)
  - Better developer experience
- **Impact:**
  - Breaking change requiring schema version bump (1.3.0 → 2.0.0)
  - All 6 data files need update: monsters, equipment, spells, tables, lineages, classes
  - Consumer code needs update to use entity-specific keys
  - Must be applied consistently in single version (no partial migration)
- **Implementation:**
  - Update `_wrap_with_meta()` in `build.py` to accept entity type parameter
  - Change `{"items": [...]}` to `{entity_type: [...]}`
  - Update all test fixtures to match new structure
  - Document in CHANGELOG as breaking change
- **Suggested for:** v0.9.0 or v1.0.0 (after classes stabilize)

**Phase 3: Add Validation**
- Create test to verify field order in output files
- Check that identification fields come before metadata
- Ensure consistent ordering across all JSON outputs

**Phase 4: Implement Helpers**
```python
def ordered_meta(*, source, ruleset_version, license, build, **kwargs):
    """Generate meta.json with consistent field ordering."""
    return OrderedDict([
        ("source", source),
        ("ruleset_version", ruleset_version),
        ("license", license),
        ("build", build),
        *kwargs.items()
    ])
```

**Phase 5: Use `json.dumps(sort_keys=True)` Strategically**
- Consider sorting keys alphabetically within sections
- Or maintain manual `OrderedDict` for semantic ordering
- Trade-off: alphabetical is stable but not semantic

### Related Work

- Python 3.7+ guarantees dict insertion order (but not serialization order)
- `dataclasses` with `asdict()` preserve field definition order
- Could use Pydantic models for structured data with guaranteed ordering

### Benefits

- Consistent, predictable JSON structure
- Easier for humans to read and compare
- Semantic ordering makes core fields immediately visible
- Git diffs more meaningful with stable ordering

### Deferred Because

- Not urgent - functionality works fine
- Requires careful review of all JSON output code
- Need to decide: semantic ordering vs alphabetical
- v0.8.1 already addressed worst issue (`version` → `ruleset_version` + reordering)

---

## DATA_DICTIONARY.md: Auto-Generation vs Manual Curation

**Context:** Two approaches exist:
1. **`scripts/generate_data_dictionary.py`** - Auto-generates basic field documentation from JSON schemas (like Swagger/OpenAPI)
2. **`docs/DATA_DICTIONARY.md`** - Manually curated with rich context (SRD transformations, extraction notes, domain knowledge)

**Current State:**
- Generation script exists but **NOT integrated** into build
- Current DATA_DICTIONARY.md is **manually maintained**
- Manual version has valuable context the generator can't produce:
  - SRD terminology mappings (e.g., "Versatile (1d8)" → `versatile_damage`)
  - Data transformation explanations (e.g., "11 + Dex modifier" → `{base: 11, dex_bonus: true}`)
  - Extraction notes and quality issues
  - Cross-dataset patterns and design decisions

**Decision (v0.8.2):**
- Keep manual curation for now
- Manual approach provides better developer experience
- Added tables, lineages, and classes sections manually (v0.8.2)

**Future Considerations:**
- Could hybrid: auto-generate field lists + manual annotations
- Could integrate generator as validation (check for missing fields)
- Could use generator for initial scaffolding of new dataset sections
- Need to resolve before declaring one approach "official"

**Action:** Revisit in v0.9.0 or v1.0.0 when documentation strategy solidifies

---

## Combined Spell Indexes (e.g., by_ritual + by_class)

**Idea:** Pre-build nested indexes for common combined queries like "ritual spells for wizard"

**Current Approach:** Flat indexes - client-side filtering
```javascript
// Current: Client-side intersection
const ritualSpells = index.spells.by_ritual.true;  // 29 spells
const wizardSpells = index.spells.by_class.wizard; // ~80 spells
const wizardRituals = ritualSpells.filter(id => wizardSpells.includes(id));
```

**Alternative:** Nested indexes
```json
"by_class_ritual": {
  "wizard": {
    "true": ["spell:detect_magic", "spell:identify", ...],
    "false": [...]
  }
}
```

**Decision:** Keep flat structure (client-side filtering preferred)

**Rationale:**
- Client-side filtering is efficient with small datasets (29 rituals, ~50-80 spells per class)
- Flexible - consumers can combine ANY two dimensions without pre-building every combination
- Keeps index.json simple and maintainable
- Avoids combinatorial explosion (ritual×class, concentration×school, ritual×level, etc.)
- `by_class` is the primary use case and we have it!

**If needed later:** Consumers can build their own derived indexes on first load

---

## Class Progression Table Extraction - Known Limitations (v0.9.8)

**Date Raised:** 2025-11-06
**Status:** Documented - minor cosmetic issues, functionally complete
**Priority:** LOW - deferred cleanup
**Version:** v0.9.8 (4 of 12 classes complete)

### Context

During extraction of simple class progression tables (Barbarian, Fighter, Monk, Rogue), discovered two minor data quality issues:

### 1. Monk Row 6: Soft Hyphen in "Ki-Empowered Strikes" (PDF Artifact)

**Current Output:**
```json
"Ki-­‐Empowered Strikes, Monastic Tradition feature"
```

**Issue:** Contains soft hyphen characters (U+00AD and U+2010) in "Ki-­Empowered"

**Root Cause:**
- These characters exist in the source PDF (page 26)
- PDF uses soft hyphens for line-break formatting hints
- **This is accurate extraction** - we're faithfully capturing what's in the PDF

**Impact:**
- Minor cosmetic issue
- May cause display issues in some renderers
- Text search for "Ki-Empowered" works with proper Unicode handling
- Data structure is valid

**Possible Solutions:**
1. Strip all soft hyphens in postprocessing (simple)
2. Normalize Unicode to NFKD form (removes formatting hints)
3. Manual text cleanup in postprocess for known cases

**Decision:** Deferred to future cleanup pass
- Not blocking any functionality
- Affects 1 cell in 1 table
- Other tables may have similar PDF formatting artifacts
- Could be addressed in a text normalization pass

### 2. Rogue Row 10: Missing "Improvement" in "Ability Score Improvement" (Extraction Limitation)

**Current Output:**
```json
["10th", "+4", "5d6", "Ability Score"]
```

**Expected:**
```json
["10th", "+4", "5d6", "Ability Score Improvement"]
```

**Issue:** The word "Improvement" is missing from row 10, Features column - **this is incomplete extraction**

**Root Cause:**
- Rogue table spans pages 39-40 with complex layout
- Row 10 ends at bottom of page 39 with "Ability Score"
- Word "Improvement" appears on page 40 at y=71.9 as continuation text
- Right column (11th-20th) starts at y=72, just below the continuation text
- Continuation text is being picked up as part of row 11 structure instead of merging with row 10
- **This is an extraction limitation** - we're not successfully merging cross-page continuation text

**Impact:**
- Minor data quality issue
- Meaning is clear from context (all other ASI rows say "Ability Score Improvement")
- Does not affect table structure (still 20 rows)
- Consumers can infer full text from level 4, 8, 12, 16, 19 ASI entries

**Technical Challenge:**
- Continuation text crosses page boundary (39 → 40)
- Continuation is in different region (left column page 39 → right column page 40)
- Current merge_continuation_rows logic works within regions, not across pages
- Would require complex cross-page, cross-region continuation merging logic

**Possible Solutions:**
1. Enhanced continuation merging across page boundaries (complex)
2. Special case handling for known page breaks (brittle)
3. Manual text fixup in postprocessing (hardcoding)
4. Accept as limitation and document (current approach)

**Decision:** Documented limitation, deferred to future enhancement
- Affects 1 cell in 1 table
- Context makes meaning clear
- Cross-page merging is complex and risky
- Not worth the effort for single word

### Related Patterns

These issues have different natures:
- **Soft hyphens:** PDF formatting artifacts that we accurately extract (cosmetic cleanup opportunity)
- **Cross-page continuation:** Extraction limitation where we fail to merge text across page boundaries

Both may recur in spellcaster class tables (wider, more complex layouts). Will track similar issues and address in batch if pattern emerges.

### Documentation

**Locations:**
1. ✅ `src/srd_builder/table_extraction/table_metadata.py` - In-code notes field for Monk and Rogue configs
2. ✅ `docs/ROADMAP.md` - v0.9.8 section under "Known Limitations"
3. ✅ `docs/PARKING_LOT.md` - This section (comprehensive technical details)
4. ⏳ Bundle README.md - User-facing documentation (to be added)

### Future Work

**When to Address:**
1. **Soft hyphens:** During text normalization/cleanup pass (v0.12.0 polish?)
2. **Cross-page continuation:** If pattern emerges in spellcaster tables, prioritize fix
3. **Both:** If consumer feedback indicates issues with data quality

**Don't address until:**
- Spellcaster tables complete (see if pattern recurs)
- Other PDF formatting artifacts identified (batch fix)
- Consumer reports actual impact on usage

---

## [Add more parked features here as needed]
