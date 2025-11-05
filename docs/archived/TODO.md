# TODO - Known Gaps & Future Improvements

> **🗄️ ARCHIVED:** This document has been **deprecated** as of v0.8.5.
>
> **Active items moved to:**
> - **ROADMAP.md § Dataset Coverage** - Current dataset status and counts
> - **ROADMAP.md v0.13.0** - Quality & Polish milestone (final pass before v1.0.0)
> - **PARKING_LOT.md** - Deferred features and technical debt
>
> This file is preserved for historical reference only. All quality issues and improvements are now tracked in ROADMAP.md milestone sections.

---

## Historical Status (as of v0.8.2)

**Datasets Complete:**
- ✅ Monsters (296 entries, schema v1.3.0)
- ✅ Equipment (106 entries, schema v1.3.0)
- ✅ Spells (319 entries, schema v1.3.0)
- ✅ Tables (23 entries, schema v1.3.0)
- ✅ Lineages (13 entries, schema v1.3.0)
- ✅ Classes (12 entries, schema v1.3.0)

---

# Historical Content Below

This document tracked known gaps, parsing improvements, and quality issues for established datasets. Unlike ROADMAP.md (new features) and PARKING_LOT.md (deferred features), this focused on **incremental improvements** to existing data extraction.

---

## Monsters Dataset (296 entries)

### Known Gaps

#### 1. Ranged Spell Attack Range Field 🔵 **LOW PRIORITY**

**Status:** Identified in v0.8.2 review
**Impact:** Low (depends on spell dataset cross-reference)

**Current State:**
```json
{
  "name": "Hurl Flame",
  "attack_type": "ranged_spell",
  "to_hit": 5,
  "text": "Ranged Spell Attack: +5 to hit, range 150 ft., one target."
  // ❌ Missing: "range": {"normal": 150}
}
```

**Better Solution:** Cross-reference with spell dataset
- Most spell attacks reference actual spells (Fire Bolt, Ray of Frost, etc.)
- Spell range should come from spells.json, not monster actions
- Exception: Monster-specific spell-like abilities (Hurl Flame) could extract range

**User Note:** "Ranged spell attack would most likely be by spell, and that information would be provided by spell range & attack information."

**Why Deferred:** Range information properly belongs in spell dataset. Monster actions that reference spells should link to spell IDs. Only monster-specific spell-like abilities need range extraction, and these are rare (Fire Elemental's Hurl Flame is specific to that creature).

---

#### 2. Action Parsing Coverage (47% unparsed) 🔵 **MEDIUM PRIORITY**

**Status:** Baseline established in v0.5.1
**Impact:** Medium (412/884 actions without structured fields)

**Current Coverage:**
- ✅ 472/884 actions (53.4%) with `attack_type`, `to_hit`, `damage`
- ❌ 412/884 actions (46.6%) unparsed (non-attack actions)

**Unparsed Action Types:**
1. **Multiattack** (very common) - No structured parsing needed
2. **Utility actions** - Grapple, Shove, Dash, etc.
3. **Buff/debuff actions** - Frighten, Charm, Polymorph
4. **Movement actions** - Teleport, Etherealness, Burrowing

**Opportunities:**
- Parse ability checks (Grapple: contested Strength check)
- Parse condition infliction (Frightening Presence: DC 15 Wisdom save or frightened)
- Already handled in `saving_throw` field for many actions

**Why Deferred:** Non-attack actions are less critical for combat automation. Structured data exists via `saving_throw` field for most debuffs.

---

#### 3. Legendary Action Cost Parsing 🔵 **LOW PRIORITY**

**Status:** Identified but not critical
**Impact:** Low (30 legendary creatures, ~90 legendary actions)

**Current State:**
```json
{
  "name": "Paralyzing Touch (Costs 2 Actions)",
  "simple_name": "paralyzing_touch_costs_2_actions",
  "text": "The lich uses its Paralyzing Touch."
}
```

**Target State:**
```json
{
  "name": "Paralyzing Touch",
  "simple_name": "paralyzing_touch",
  "action_cost": 2,
  "text": "The lich uses its Paralyzing Touch."
}
```

**Implementation:**
- Extract "(Costs X Actions)" from action name
- Store in `action_cost` field (default 1 if not specified)
- Clean name to remove cost annotation
- Update `parse_monsters.py` legendary action parsing

**Why Deferred:** Legendary action economy is clear from text. Cost is typically 1 (most common) or explicitly stated in name. Not blocking for combat automation.

---

#### 4. Spellcasting Trait Structure 🔵 **FUTURE**

**Status:** Currently text-only
**Impact:** Medium (casters need spell list parsing)

**Current State:**
```json
{
  "name": "Spellcasting",
  "text": "The archmage is an 18th-level spellcaster. Its spellcasting ability is Intelligence (spell save DC 17, +9 to hit with spell attacks). The archmage has the following wizard spells prepared:\n\nCantrips (at will): fire bolt, light, mage hand, prestidigitation, shocking grasp\n1st level (4 slots): detect magic, identify, mage armor, magic missile\n..."
}
```

**Target State:**
```json
{
  "name": "Spellcasting",
  "spellcasting": {
    "ability": "intelligence",
    "dc": 17,
    "to_hit": 9,
    "caster_level": 18,
    "spell_list": {
      "cantrips": ["fire_bolt", "light", "mage_hand", "prestidigitation", "shocking_grasp"],
      "1": {"slots": 4, "spells": ["detect_magic", "identify", "mage_armor", "magic_missile"]},
      ...
    }
  }
}
```

**Why Deferred:** Complex parsing, requires spell name → spell ID mapping. Better done after spells dataset integration (v0.6.x+). Needs cross-dataset resolution.

---

### Quality Improvements

#### Equipment References in Monster Actions 🔵 **LOW PRIORITY**

**Opportunity:** Link weapon attacks to equipment dataset

**Example:**
```json
{
  "name": "Longsword",
  "attack_type": "melee_weapon",
  "equipment_ref": "item:longsword",  // Link to equipment
  "damage": {
    "average": 7,
    "dice": "1d8+3",
    "type": "slashing"
  }
}
```

**Benefits:**
- Cross-dataset validation
- Enables equipment property lookups
- Useful for homebrew monsters with custom weapons

**Why Deferred:** Requires fuzzy matching (action name may not exactly match equipment name). Low priority for SRD-only data.

---

## Equipment Dataset (106 entries)

### Known Gaps

#### 1. Properties Normalization ⚠️ **MEDIUM PRIORITY**

**Status:** Identified by Blackmoor, deferred
**Impact:** Medium (cleaner rule automation)

**Current State:**
```json
{
  "properties": ["versatile (1d10)", "thrown (range 20/60)"]
}
```

**Target State:**
```json
{
  "properties": ["versatile", "thrown"]
  // Data already in: versatile_damage, range fields
}
```

**Implementation:**
- Strip parenthetical data from properties array
- Verify `versatile_damage` and `range` fields capture all data
- Update `parse_equipment.py` to clean properties
- Test that no data is lost

**Why Deferred:** Non-blocking. Blackmoor integration already complete. Structured fields exist for the data.

---

#### 2. Container Capacity Hardcoded Values ⚠️ **HIGH PRIORITY**

**Status:** TECHNICAL DEBT - See PARKING_LOT.md "Container Capacity Hardcoded Values"
**Impact:** High (will break when table extraction improves)

**Current State:**
- 8/13 containers extracted from PDF
- 5/13 hardcoded in `parse_equipment.py`
- Works correctly but fragile

**Root Cause:**
- Container Capacity table spans pages 69-70
- Multi-column layout confuses extraction
- Table continues mid-page

**Implementation:**
- Fix multi-column table extraction
- Remove `CONTAINER_CAPACITIES` dict
- Verify extraction captures all 13 containers

**Why Deferred:** Requires table extraction overhaul. Current solution works for consumers. Will address with general table extraction improvements.

---

#### 3. Weapon Subcategory Normalization 🔵 **LOW PRIORITY**

**Status:** Identified, cosmetic
**Impact:** Low (data is correct, just not normalized)

**Current State:**
```json
{
  "subcategory": "Martial Melee"  // Raw string from PDF
}
```

**Target State:**
```json
{
  "subcategory": "martial_melee"  // Normalized like simple_name
}
```

**User Note:** "Does the schema files have the category list or definitions? Or is this a data_dictionary that wouldn't be in the schema files?"

**Schema Investigation Results:**
- Field is `sub_category` (with underscore) in schema
- Type: `string | null` - NO enum defined
- This means values are documented in DATA_DICTIONARY.md, not constrained by schema
- Schema is intentionally flexible to allow various subcategory values

**Current Values (from data):**
- Armor: "Light Armor", "Medium Armor", "Heavy Armor"
- Weapons: "Simple Melee", "Simple Ranged", "Martial Melee", "Martial Ranged"

**Implementation:**
- Add normalization to `parse_equipment.py` to convert to lowercase + underscores
- Update DATA_DICTIONARY.md to document normalized values
- No schema changes needed (intentionally flexible)
- Update tests

**Why Deferred:** Non-blocking. Current values are clear and usable. Schema intentionally allows flexibility.

---

#### 4. Equipment Aliases 🔵 **LOW PRIORITY**

**Status:** See PARKING_LOT.md "Equipment Name Aliases"
**Impact:** Low (only 2 items affected, stay close to SRD)

**Problem:**
- "Flask or tankard" can't be found by searching "tankard"
- "Jug or pitcher" can't be found by searching "pitcher"

**User Note:** "Aliases are minor and isolated to only a couple of things we've discussed before - I also don't want to stray too far from the SRD :)"

**Solution:** Add `aliases` array (same pattern as lineages, terminology)

**Why Deferred:** Only affects 2 items. Want to stay close to SRD naming. Unified alias system exists (v0.8.1) but applying it here is low value.

---

## Spells Dataset (319 entries)

### Known Gaps

#### 1. Ritual Flag ✅ **COMPLETE**

**Status:** Fixed in v0.6.4, validated v0.8.2
**Impact:** None - complete coverage confirmed

**Current Coverage:** 29/319 ritual spells (100% - manually verified)
**Validation:** Manual count of SRD 5.1 matches extracted count exactly (29 = 29)

**Confidence:** HIGH - Exact match between manual verification and automated extraction

**Extracted Ritual Spells (29):**
Alarm, Animal Messenger, Augury, Commune, Commune with Nature, Comprehend Languages, Contact Other Plane, Detect Magic, Detect Poison and Disease, Divination, Find Familiar, Floating Disk, Forbiddance, Gentle Repose, Identify, Illusory Script, Instant Summons, Locate Animals or Plants, Magic Mouth, Meld into Stone, Phantom Steed, Purify Food and Drink, Silence, Speak with Animals, Telepathic Bond, Tiny Hut, Unseen Servant, Water Breathing, Water Walk

**Indexed:** `by_ritual` index available in index.json

---

#### 2. Area of Effect Coverage (83% unparsed) ⚠️ **MEDIUM PRIORITY**

**Status:** Baseline established in v0.6.4
**Impact:** Medium (part of complete spell pass)

**Current Coverage:**
- ✅ 55/319 spells (17%) with `effects.area`
- ❌ 264/319 spells (83%) unparsed

**User Note:** "Finishing the area of effect, healing coverage and spell range are important, medium sounds about right as I wouldn't call a complete pass until all these are done."

**Unparsed Patterns:**
1. Touch/self range spells (no area)
2. Variable area spells ("a point you choose")
3. Complex shapes ("10-foot-radius, 40-foot-high cylinder")
4. Multiple areas ("three 20-foot cubes")

**Opportunities:**
- Parse "point you choose within range" → structured
- Parse multi-part areas (cylinder: radius + height)
- Parse multiple instances (3 cubes)
- Target: >50% coverage (160+ spells)

**Why Deferred:** Current coverage handles common combat spells (Fireball, Lightning Bolt). Need focused effort for complete pass.

---

#### 3. Healing Coverage (98% unparsed) ⚠️ **MEDIUM PRIORITY**

**Status:** Baseline established in v0.6.4
**Impact:** Medium (part of complete spell pass)

**Current Coverage:**
- ✅ 5/319 spells (2%) with `effects.healing`
- ❌ Spells with fixed healing excluded (Heal, Mass Heal)

**User Note:** "Finishing the area of effect, healing coverage and spell range are important, medium sounds about right as I wouldn't call a complete pass until all these are done."

**Schema Note:**
- Current schema requires dice pattern
- Fixed-amount healing (e.g., "70 hit points") not captured

**Question:** Should fixed healing be included?

**Why Deferred:** Part of comprehensive spell effects pass. Should be completed together with area of effect and spell range.

---

#### 4. Spell Range Extraction ⚠️ **MEDIUM PRIORITY**

**Status:** Not yet implemented
**Impact:** Medium (part of complete spell pass)

**Current State:**
Spells have range in text ("Range: 120 feet") but not structured field.

**Target State:**
```json
{
  "range": {
    "value": 120,
    "unit": "feet",
    "type": "ranged"  // or "touch", "self", "sight"
  }
}
```

**User Note:** "Finishing the area of effect, healing coverage and spell range are important, medium sounds about right as I wouldn't call a complete pass until all these are done. Not sure what you by spell coverage - that sounds like area of effect which is important."

**Implementation:**
- Parse range patterns: "120 feet", "Touch", "Self", "Sight", "Unlimited"
- Extract from spell metadata line (near casting time, components)
- Add to spell schema

**Why Important:** Required for spell attack range (see Monsters TODO #1). Also critical for spell selection and targeting in VTT.

---

### Quality Improvements

#### Spell Scaling Patterns 🔵 **FUTURE**

**Opportunity:** Structured upcasting formulas

**Current State:**
```json
{
  "scaling": {
    "type": "slot_level",
    "description": "When you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d6 for each slot level above 1st."
  }
}
```

**Target State:**
```json
{
  "scaling": {
    "type": "slot_level",
    "base_level": 1,
    "per_level": {
      "damage": "+1d6"
    },
    "description": "..."
  }
}
```

**Why Deferred:** Text description sufficient for now. Structured formula needs careful pattern matching.

---

## Tables Dataset (23 entries)

### Known Gaps

#### 1. Table Extraction Quality ⚠️ **ONGOING**

**Status:** Manual extraction for v0.7.0/v0.8.2
**Impact:** High (affects container capacity, class progression)

**Current State:**
- 23 tables extracted manually
- Multi-column layouts cause issues
- Page breaks mid-table lose context

**See:** PARKING_LOT.md "Container Capacity Hardcoded Values"

**Improvements Needed:**
- Multi-column detection
- Table continuation across pages
- Column boundary detection
- Section header filtering

**Why Ongoing:** Table extraction is complex. Manual approach works but doesn't scale.

---

#### 2. Table Coverage Validation 🔵 **FUTURE**

**Opportunity:** Validate extracted vs expected tables

**Implementation:**
- Compare extracted table count to `table_targets.py`
- Flag missing tables
- Verify row counts match expectations
- Cross-reference with table indexer metadata

**Why Deferred:** Current extraction is manual and verified. Automation needed when extraction becomes automatic.

---

## Lineages Dataset (13 entries)

### Known Gaps

#### 1. Subrace Trait Inheritance 🔵 **LOW PRIORITY**

**Status:** Identified, structure exists
**Impact:** Low (4 subraces in SRD)

**Current State:**
- Subraces have `parent_lineage` field
- Traits are duplicated (e.g., High Elf has Darkvision + Elf Weapon Training)

**Question:** Should subrace traits reference parent traits or duplicate?

**User Note:** "Not sure what you mean by subrace trait inheritance. But it seems low is good."

**Clarification:** High Elf inherits base Elf traits (Darkvision) plus gets additional traits (Elf Weapon Training). Currently we duplicate all traits in the High Elf record rather than saying "inherit from parent". This works fine and is simpler for consumers.

**Considerations:**
- Duplication: Simpler for consumers, no resolution needed (current approach)
- Reference: DRY, but requires parent lookup
- Current approach (duplication) is pragmatic

**Why Deferred:** Current structure works. 4 subraces is small dataset. Duplication is clearer than inheritance.

---

#### 2. Lineage Aliases 🔵 **IMPLEMENTED IN v0.8.1**

**Status:** COMPLETE ✅
**Impact:** High (backward compatibility)

**Implementation:**
- Index-level aliases: `{"races": "lineages", "race": "lineage"}`
- Entity-level aliases: Optional `aliases` field in lineage records
- Automatic expansion in `by_name` index

**Why Complete:** Part of comprehensive alias system in v0.8.1

---

## Classes Dataset (12 entries)

### Known Gaps

#### 1. Feature References 🔵 **FUTURE**

**Status:** Deferred to v0.10.0 (Features Dataset)
**Impact:** Medium (would enable cross-referencing)

**Current State:**
```json
{
  "features": [
    "feature:fighting_style",
    "feature:second_wind",
    "feature:action_surge"
  ]
}
```

**Question:** Should these link to standalone feature entities?

**User Note:** "Yeah, breaking features out separate makes that a dependency. These feel like they are highly dependent on rules.json and that is on the roadmap."

**Depends On:**
- Features dataset extraction (v0.10.0)
- Rules dataset (v0.11.0) - feature mechanics and rule text

**Why Deferred:** Features dataset doesn't exist yet. Will likely require Rules dataset (v0.11.0) for complete feature mechanics. IDs are future-proofing for cross-dataset links.

---

#### 2. Multiclassing Prerequisites 🔵 **FUTURE**

**Status:** Not in SRD 5.1
**Impact:** Low (variant rule, not in core SRD)

**Note:** Multiclassing prerequisites are in DMG, not SRD. Not applicable for v1.0.0 (SRD 5.1 complete).

---

#### 3. Subclass Data 🔵 **FUTURE**

**Status:** Minimal in SRD (1 subclass per class)
**Impact:** Low (SRD has limited subclasses)

**Current State:**
```json
{
  "subclasses": [
    "subclass:champion"  // Fighter only subclass in SRD
  ]
}
```

**Note:** Full subclass extraction would require PHB. SRD has 1 subclass per class (example only).

---

## Cross-Dataset Improvements

### 1. ID Resolution & Validation 🔵 **FUTURE**

**Opportunity:** Validate references across datasets

**Examples:**
- Class features reference spell IDs
- Monster spellcasting references spell IDs
- Equipment actions reference equipment IDs

**Implementation:**
- Cross-dataset validation pass
- Flag broken references
- Build dependency graph

**Why Deferred:** Requires all datasets complete. Should be part of v1.0.0 validation.

---

### 2. Unified Alias System ✅ **IMPLEMENTED IN v0.8.1**

**Status:** COMPLETE
**Impact:** High (discoverability, backward compatibility)

**Implementation:**
- Three-level aliases: index-level, entity-level, indexer-level
- Terminology aliases in `index.json`
- Entity aliases in data records
- Automatic expansion in lookups

**Why Complete:** Comprehensive system shipped in v0.8.1

---

### 3. Data Dictionary Automation 🔵 **DEFERRED**

**Status:** See PARKING_LOT.md "DATA_DICTIONARY.md: Auto-Generation vs Manual Curation"
**Impact:** Low (documentation quality-of-life)

**Current State:**
- Manual curation with rich context
- Generation script exists but not integrated

**Decision:** Keep manual for now, revisit in v0.9.0/v1.0.0

---

## Schema Evolution

### Breaking Changes Needed (v2.0.0)

1. **Semantic Entity Keys** (PARKING_LOT.md)
   - `{"items": [...]}` → `{"monsters": [...]}`
   - Impacts all 6 data files
   - Better developer experience

2. **Saving Throw Objects** (PARKING_LOT.md)
   - `"DC 14 Constitution"` → `{dc: 14, ability: "constitution"}`
   - Impacts monsters, spells
   - Enables automated resolution

### Additive Changes (v1.x)

1. **Ranged spell attack range** (monsters)
2. **Properties normalization** (equipment)
3. **Equipment aliases** (equipment)
4. **Legendary action cost** (monsters)

---

## Priority Legend

- ⚠️ **HIGH PRIORITY** - Blocking for Blackmoor or causing technical debt
- 🔵 **MEDIUM PRIORITY** - Nice-to-have, improves quality
- 🔵 **LOW PRIORITY** - Cosmetic or edge case
- 🔵 **FUTURE** - Deferred to v1.0.0+ or next dataset

---

## How to Use This Document

1. **Before starting a new version:** Review TODO items for target datasets
2. **When fixing bugs:** Check if issue is documented here
3. **When improving parsing:** Mark items as COMPLETE ✅
4. **When identifying new gaps:** Add to appropriate dataset section
5. **When planning breaking changes:** Note schema version impact

**Related Documents:**
- `ROADMAP.md` - New features and datasets
- `PARKING_LOT.md` - Deferred features and technical debt
- `CHANGELOG.md` - Historical changes
- `DATA_DICTIONARY.md` - Field documentation
