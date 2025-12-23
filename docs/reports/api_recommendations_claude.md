Perfect context - that helps tremendously. Let me examine these APIs systematically.Let me fetch actual sample responses from the dnd5eapi to see their data structure:Now let me look at some actual API responses to understand the data structures better:Let me check your GitHub repo structure:Now let me look at sample outputs from the different APIs to compare data structures. Let me search for specific endpoint examples:Based on my research, I'll now compile a comprehensive analysis. Let me create a structured document for you:I've completed a comprehensive analysis comparing your SRD-Builder against dnd5eapi.co, 5e-bits, and Open5e. Here are the key takeaways:

## Your Main Strengths
- **Source provenance with page numbers** - None of them have this
- **Deterministic, reproducible builds** - Essential for legal compliance
- **Offline-first design** - Perfect for solo gaming
- **Clean extraction pipeline** - Easy to debug and extend

## Critical Gaps for Solo Gaming
1. **Cross-references missing** - Can't navigate spell → condition or monster → skill relationships
2. **No computed stats** - Missing ability modifiers, attack bonuses
3. **Subclasses incomplete** - Have base classes but missing subclass progressions

## Recommendations
**Phase 1 (v0.18-0.19):** Add cross-reference infrastructure
- Create atomic datasets (skills.json, damage_types.json, ability_scores.json)
- Add reference IDs to existing datasets
- Build cross-dataset indexes

**Phase 2 (v0.20):** Computed fields
- Ability modifiers
- Proficiency bonuses
- Attack bonuses

**Don't try to be dnd5eapi** - they're optimized for online VTTs. You should be the **"auditable, offline-first dataset for solo gaming"** - which is a defensible niche they don't serve.

The analysis includes specific JSON structure examples, a detailed endpoint coverage matrix, and prioritized action items. What questions do you have about the findings or recommendations?

Excellent! This is exactly what I needed. Now I can give you **concrete, tactical recommendations** based on your actual implementation.

## Your Current State: Better Than I Thought!

You already have:
✅ **Working cross-reference system** (feature IDs, class→feature links)
✅ **Bidirectional indexes** (indexer builds reverse lookups)
✅ **ID conventions** (feature:rage pattern)
✅ **Schema validation** framework

You're **not starting from zero** - you have the infrastructure, just need to **extend the pattern** to more relationships.

## Concrete v1.0 Roadmap (Based on Actual Code)

### Priority 1: Complete Existing Patterns (v0.18)
**Goal:** Apply the `classes → features` pattern to other datasets

#### 1a. Lineages → Features Link
```python
# In parse_lineages.py (or postprocessor)
lineage["features"] = [
    "feature:darkvision",
    "feature:dwarven_resilience",
    ...
]
```

**Files to modify:**
- `src/srd_builder/parse/parse_lineages.py` (or create postprocessor)
- `schemas/lineage.schema.json` (add features array)
- `src/srd_builder/assemble/indexer.py` (add lineages.by_feature)

**Effort:** ~2-3 hours (pattern already exists in classes)

#### 1b. Spells → Conditions Link
```python
# In postprocess_spells.py
spell["inflicts_conditions"] = ["condition:paralyzed"]
spell["requires_conditions"] = ["condition:unconscious"]  # for revivify
```

**Detection strategy:** Parse spell descriptions for condition keywords
- Match against conditions.json names
- Add to schema as optional arrays

**Files to modify:**
- `src/srd_builder/postprocess/postprocess_spells.py`
- `schemas/spell.schema.json`
- `src/srd_builder/assemble/indexer.py` (add `spells.by_condition_inflicted`)

**Effort:** ~4-6 hours (need text parsing logic)

### Priority 2: High-Value New Links (v0.19)

#### 2a. Monsters → Spells (Innate Spellcasting)
**Current state:** Spellcasting is embedded in traits as text

**Proposed:**
```json
{
  "id": "monster:drow",
  "traits": [...],  // Keep existing
  "spells": {
    "innate": {
      "ability": "charisma",
      "dc": 11,
      "at_will": ["spell:dancing_lights", "spell:darkness"],
      "per_day": {
        "1": ["spell:faerie_fire", "spell:levitate"]
      }
    }
  }
}
```

**Implementation:**
- Parse monster traits for spellcasting sections
- Extract spell names, match to spells.json
- Store as structured object

**Files to modify:**
- `src/srd_builder/parse/parse_monsters.py` (or new `parse_monster_spells.py`)
- `schemas/monster.schema.json` (add optional spells field)
- Indexer (add `monsters.by_spell_known`)

**Effort:** ~1-2 days (complex parsing, but high value)

#### 2b. Magic Items → Spells
```json
{
  "id": "magic_item:wand_of_fireballs",
  "grants_spells": [
    {
      "spell_id": "spell:fireball",
      "charges": 7,
      "level": 3
    }
  ]
}
```

**Files to modify:**
- `src/srd_builder/postprocess/postprocess_magic_items.py`
- `schemas/magic_item.schema.json`

**Effort:** ~3-4 hours (simpler than monsters)

### Priority 3: Atomic Reference Datasets (v0.20)

#### 3a. Skills Dataset
**Purpose:** Make skill→ability relationship explicit

```json
// skills.json
{
  "_meta": {"schema_version": "1.0.0"},
  "items": [
    {
      "id": "skill:perception",
      "simple_name": "perception",
      "name": "Perception",
      "ability": "wisdom",
      "description": "Your Wisdom (Perception) check...",
      "page": 178
    }
  ]
}
```

**Extraction:** Parse "Using Ability Scores" chapter in SRD

**Files to create:**
- `src/srd_builder/extract/extract_skills.py`
- `src/srd_builder/parse/parse_skills.py`
- `schemas/skill.schema.json`

**Effort:** ~4-6 hours (small dataset, well-defined structure)

**Benefits:**
- Monsters can reference `skill:perception` instead of string "Perception"
- Indexer can build "creatures proficient in Perception"

#### 3b. Damage Types Dataset
```json
// damage_types.json
{
  "items": [
    {
      "id": "damage_type:fire",
      "name": "Fire",
      "description": "...",
      "page": 196
    }
  ]
}
```

**Extraction:** Parse "Damage Types" section

**Effort:** ~2-3 hours (13 items, straightforward)

#### 3c. Ability Scores Dataset
```json
// ability_scores.json (6 items)
{
  "items": [
    {
      "id": "ability:strength",
      "abbreviation": "STR",
      "name": "Strength",
      "description": "...",
      "skills": ["skill:athletics"],
      "page": 175
    }
  ]
}
```

**Effort:** ~2-3 hours

### Priority 4: Computed Fields (v0.21)

#### Add Ability Modifiers
```python
# In postprocess_monsters.py
def add_ability_modifiers(monster):
    for ability, score in monster["ability_scores"].items():
        modifier_key = f"{ability}_modifier"
        monster["ability_scores"][modifier_key] = (score - 10) // 2
```

**Update schema:**
```json
"ability_scores": {
  "type": "object",
  "properties": {
    "strength": {"type": "integer"},
    "strength_modifier": {"type": "integer"},  // Add this
    ...
  }
}
```

**Effort:** ~2 hours (simple math, update schemas)

### Priority 5: Enhanced Cross-Reference Indexes (v0.22)

#### Extend indexer.py with reverse lookups
```python
# In assemble/indexer.py

def build_cross_references(datasets):
    cross_refs = {
        "conditions_inflicted_by": defaultdict(list),
        "spells_granted_by_item": defaultdict(list),
        "creatures_with_spell": defaultdict(list),
    }

    # Spells → Conditions
    for spell in datasets["spells"]["items"]:
        for condition_id in spell.get("inflicts_conditions", []):
            cross_refs["conditions_inflicted_by"][condition_id].append(spell["id"])

    # Magic Items → Spells
    for item in datasets["magic_items"]["items"]:
        for spell_ref in item.get("grants_spells", []):
            spell_id = spell_ref["spell_id"]
            cross_refs["spells_granted_by_item"][spell_id].append(item["id"])

    return cross_refs
```

**Effort:** ~4-6 hours (extend existing indexer)

---

## Proposed v1.0.0 Milestone Checklist

```markdown
## v0.18.0 - Complete Existing Patterns (1 week)
- [ ] Link lineages → features (like classes do)
- [ ] Add spells.inflicts_conditions array
- [ ] Add spells.requires_conditions array
- [ ] Update schemas
- [ ] Extend indexer with new lookups

## v0.19.0 - Monster/Item Spell Links (1.5 weeks)
- [ ] Parse monster innate spellcasting to structured format
- [ ] Add monsters.spells field
- [ ] Link magic items → spells they grant
- [ ] Update schemas

## v0.20.0 - Atomic Reference Datasets (1 week)
- [ ] Extract skills.json (18 items)
- [ ] Extract damage_types.json (13 items)
- [ ] Extract ability_scores.json (6 items)
- [ ] Create schemas for each
- [ ] Update indexer

## v0.21.0 - Computed Fields (3 days)
- [ ] Add ability modifiers to monsters
- [ ] Add ability modifiers to classes
- [ ] Add proficiency bonuses to monsters (CR-based)
- [ ] Update schemas

## v0.22.0 - Enhanced Indexes & Validation (1 week)
- [ ] Add cross_references section to index.json
- [ ] Build reverse lookup indexes
- [ ] Add validation for dangling references
- [ ] Write integration tests

## v0.23.0 - Documentation & Polish (1 week)
- [ ] Comprehensive DATA_DICTIONARY.md
- [ ] Python integration examples
- [ ] JavaScript integration examples
- [ ] Reddit announcement draft
- [ ] Update README with v1.0 features

## v1.0.0 - Release 🚀
- [ ] All datasets validated
- [ ] All cross-references tested
- [ ] Documentation complete
- [ ] Announcement published
```

**Total effort:** ~6-7 weeks of focused work

---

## Immediate Next Steps

Would you like me to:

1. **Draft specific GitHub issues** for v0.18 tasks (lineages→features, spells→conditions)?
2. **Write the actual parser code** for one of these (e.g., `postprocess_spells.py` condition detection)?
3. **Design the schema changes** needed for each priority?
4. **Create a validation test** that checks cross-reference integrity?

Pick one and I'll give you something you can commit today. The key is: **you have the infrastructure, now it's just extending the pattern you already established with classes→features.**
