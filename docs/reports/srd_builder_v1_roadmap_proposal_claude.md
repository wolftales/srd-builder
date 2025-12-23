# SRD-Builder v1.0 Roadmap
**Based on Code Review & Multi-Version Strategy**
**Updated with Gemini Audit Findings**

Date: December 22, 2024

---

## 🚨 Critical Quality Issues (From Gemini Audit)

**Gemini conducted a comprehensive audit** and identified **blocking bugs** that must be fixed before v1.0:

### BLOCKER #1: Spell Descriptions Missing/Truncated
- **Impact:** Majority of spells have incomplete descriptions
- **Examples:** "Cure Wounds", "Hold Person" missing main text
- **Root cause:** Extraction/parsing pipeline drops text blocks
- **Fix required:** Debug `extract_spells.py` and `parse_spell_records.py`
- **Timeline:** 2-3 days (**v0.17.1 hotfix**)

### BLOCKER #2: Equipment Pack References Broken
- **Impact:** Packs reference 4+ items that don't exist in equipment.json
- **Example:** "Priest's Pack" points to non-existent items
- **Fix required:** Add missing items OR remove from packs
- **Timeline:** 1-2 days (**v0.17.1 hotfix**)

### HIGH PRIORITY: Test Coverage Gaps
- **Impact:** 0% coverage in `parse_madness.py`, `parse_poisons.py`, `table_indexer.py`
- **Consequence:** Spell bug went undetected; likely more issues lurking
- **Fix required:** Comprehensive tests for all parse modules
- **Timeline:** Integrated into **v0.22** (2-3 days)

### HIGH PRIORITY: Security Vulnerabilities
- **Impact:** 8 known vulnerabilities in dependencies (pypdf, pdfminer-six, filelock, pip)
- **Fix required:** Update to safe versions
- **Timeline:** Integrated into **v0.18** (2-3 hours)

### MEDIUM: Type Checking Too Lenient
- **Impact:** 21 functions have no type hints, mypy doesn't catch them
- **Fix required:** Enable `disallow_untyped_defs = true`
- **Timeline:** Integrated into **v0.22** (1 day)

**Result:** Timeline extended from 6.5 weeks → **8.5 weeks** to address quality issues.

---

## Current State (v0.17.0)

### What You Already Have ✅
- **11 datasets complete:** monsters, spells, equipment, magic_items, classes, lineages, conditions, diseases, poisons, features, tables, rules
- **System metadata:** Every file has `source`, `ruleset_version`, `schema_version`
- **Two cross-reference patterns working:**
  1. Simple ID arrays: `classes.features = ["feature:rage", ...]`
  2. Detailed objects: `pack_contents = [{item_id: "...", quantity: 1}]`
- **Rich table metadata:** category, section, summary fields
- **Provenance tracking:** Page numbers for every entry
- **Deterministic builds:** Reproducible from source PDF

### The Cross-Linking Theme 🔗

**Key Insight:** You've established the patterns, now it's about **extending them consistently**.

Your v1.0 journey is primarily about **completing the reference graph**:
- ✅ Classes → Features (done)
- ✅ Equipment Packs → Items (done)
- 🎯 Lineages → Features (v0.18)
- 🎯 Spells → Conditions (v0.18)
- 🎯 Monsters → Innate Spells (v0.18)
- 🎯 Magic Items ↔ Equipment (v0.19)
- 🎯 Cross-dataset indexes (v0.22)

**This makes your data navigable**, not just queryable.

### Strategic Position
**Niche:** "Auditable, offline-first D&D dataset with source provenance"
- Not competing with dnd5eapi's REST API
- Targeting solo gaming, academic research, legal compliance use cases
- Multi-version ready (5.1 → 5.2.1 → OGL planned)

---

## The 5.2.1 Test: Your Real Architecture Challenge

**Key Insight:** Adding SRD 5.2.1 is your **multi-version proof of concept**, not Pathfinder.

### Why 5.2.1 Matters
- Tests terminology aliasing (race → species)
- Reveals what data structures need version flexibility
- Shares ~95% content with 5.1 (manageable diff)
- Lets you discover breaking changes before Pathfinder

### Questions 5.2.1 Will Answer
1. Do IDs need version prefixes? (`dnd51:monster:aboleth` vs global `monster:aboleth`)
2. Can apps load both versions simultaneously?
3. Which fields changed and why?
4. Is your schema flexible enough?

**Recommendation:** Get v1.0 (5.1 complete) out, then immediately tackle 5.2.1 as v1.1. **This informs v2.0 architecture** without premature optimization.

---

## v1.0 Roadmap: 6-7 Weeks

---

## Critical Quality Pass (Before v0.18)

### v0.17.1 - Data Quality Hotfix (3-5 days) 🚨
**Goal:** Fix critical data integrity bugs discovered in audit

**BLOCKER 1: Spell Descriptions Missing**
```python
# Issue: Many spells have truncated/missing descriptions
# Example failures:
# - "Cure Wounds": only has "At Higher Levels" text
# - "Hold Person": description field empty

# Investigation targets:
# - src/srd_builder/extract/extract_spells.py
# - src/srd_builder/parse/parse_spell_records.py

# Root cause likely: Text extraction stops at certain markers
```

**Tasks:**
1. Debug spell extraction pipeline (2-3 days)
   - Add verbose logging to extract_spells.py
   - Check if description text is in raw extraction
   - Verify parse_spell_records correctly assembles text blocks

2. Add regression test (1 hour)
   - Golden file test for "Cure Wounds" full description
   - Add assertion: no spell can have empty description
   - Add to CI

**BLOCKER 2: Equipment Pack References**
```python
# Issue: Priest's Pack references 4 items not in equipment.json
# Impact: Breaks referential integrity

# Example: pack_contents might reference:
# - "item:holy_water" (doesn't exist in equipment.json)
# - "item:prayer_book" (doesn't exist)
```

**Tasks:**
1. Find missing items (1 day)
   - Parse SRD for referenced items
   - Determine if they're genuinely equipment or should be removed
   - Either add to equipment.json OR remove from pack

2. Add validation (1 hour)
   ```python
   def test_pack_references_valid(equipment, packs):
       """All pack_contents.item_id must exist in equipment"""
       equipment_ids = {item['id'] for item in equipment['items']}

       for pack in packs['items']:
           for item_ref in pack.get('pack_contents', []):
               assert item_ref['item_id'] in equipment_ids, \
                   f"{pack['name']}: {item_ref['item_id']} not found"
   ```

**BLOCKER 3: Add Critical Validation Tests**

```python
# tests/test_data_integrity.py (NEW FILE)

def test_no_empty_descriptions():
    """No dataset can have empty description/text fields"""
    for spell in spells['items']:
        assert spell.get('description'), f"{spell['name']} missing description"

def test_cross_references_resolve():
    """All ID references must point to existing entities"""
    # Test pack → equipment
    # Test class → features
    # (Will expand in v0.22)
```

**Effort:** 3-5 days total
- Spell fix: 2-3 days (debugging + testing)
- Equipment packs: 1-2 days (research + validation)

**Deliverable:** Data integrity restored, regression tests in place

---

### v0.18.0 - Extend Cross-References + Security (1.5 weeks)
**Goal:** Apply existing patterns to more relationships + remediate security vulnerabilities

#### Security Dependency Updates (from Gemini audit)

**Finding:** 8 known vulnerabilities across pypdf, pdfminer-six, filelock, pip

**Tasks:**
1. Update vulnerable dependencies in pyproject.toml (30 min)
2. Test build pipeline with updates (1 hour)
3. Add pip-audit to CI pipeline (30 min)

**Effort:** 2-3 hours (parallel with cross-reference work)

#### Cross-Reference Tasks
1. **Lineages → Features** (copy classes pattern)
   ```json
   // lineages.json
   {
     "id": "lineage:dwarf",
     "features": [  // ← Add this array
       "feature:darkvision",
       "feature:dwarven_resilience",
       "feature:stonecunning"
     ]
   }
   ```
   - **Files:** `parse_lineages.py`, `lineage.schema.json`, `indexer.py`
   - **Effort:** 2-3 hours (pattern already exists)

2. **Spells → Conditions** (detect from descriptions)
   ```json
   // spells.json
   {
     "id": "spell:hold_person",
     "inflicts_conditions": [
       {
         "condition_id": "condition:paralyzed",
         "duration": "1 minute",
         "save_ends": true
       }
     ]
   }
   ```
   - **Files:** `postprocess_spells.py`, `spell.schema.json`
   - **Detection:** Parse description for condition keywords
   - **Effort:** 4-6 hours

3. **Monsters → Innate Spells** (parse spellcasting traits)
   ```json
   // monsters.json
   {
     "id": "monster:drow",
     "innate_spellcasting": {
       "ability": "charisma",
       "dc": 11,
       "spells": [
         {
           "spell_id": "spell:dancing_lights",
           "spell_name": "Dancing Lights",  // Inline for display
           "frequency": "at_will"
         },
         {
           "spell_id": "spell:faerie_fire",
           "spell_name": "Faerie Fire",
           "frequency": "per_day",
           "uses": 1
         }
       ]
     }
   }
   ```
   - **Files:** `parse_monsters.py` (or new `parse_monster_spells.py`), `monster.schema.json`
   - **Pattern:** Copy equipment pack structure (detailed objects)
   - **Effort:** 1-2 days (complex parsing)

4. **Magic Items → Spells** (simpler parsing)
   ```json
   {
     "id": "magic_item:wand_of_fireballs",
     "grants_spells": [
       {
         "spell_id": "spell:fireball",
         "spell_name": "Fireball",
         "charges": 7,
         "spell_level": 3
       }
     ]
   }
   ```
   - **Files:** `postprocess_magic_items.py`, `magic_item.schema.json`
   - **Effort:** 3-4 hours

**Deliverable:** All major cross-references working within datasets

---

### v0.19.0 - Property Normalization + Magic Item Links (1 week)
**Goal:** Convert string properties to structured objects AND link magic items to their mundane bases

#### Magic Items ↔ Equipment Cross-Linking

**Problem:** Magic items are often enchanted versions of mundane equipment, but no relationship exists.

```json
// equipment.json - Add this
{
  "id": "item:longsword",
  "name": "Longsword",
  "magical_variants": [  // ← NEW
    "magic_item:longsword_plus_1",
    "magic_item:flame_tongue"
  ]
}

// magic_items.json - Add this
{
  "id": "magic_item:longsword_plus_1",
  "name": "Longsword, +1",
  "base_item_id": "item:longsword",      // ← NEW
  "base_item_name": "Longsword",         // ← NEW (inline display)
  "inherits_from_base": ["damage", "properties", "weight"],  // ← NEW
  "rarity": "uncommon",
  "modifiers": {
    "attack_bonus": 1,
    "damage_bonus": 1
  }
}
```

**Implementation:**
- Detection logic: Parse magic item names for base equipment patterns
  - "Longsword, +1" → "Longsword"
  - "Armor (plate)" → "Plate Armor"
  - "Sword of Sharpness" → "Longsword" (harder, may need manual mapping)
- Bidirectional: magic_items get `base_item_id`, equipment gets `magical_variants`
- **Files:** `postprocess_equipment.py`, `postprocess_magic_items.py`, both schemas
- **Effort:** 4-6 hours

**Benefits:**
- Apps can query "all longsword variants"
- Magic item stats can inherit from base (damage, weight, etc.)
- Supports edge cases (amulets have no mundane base → `base_item_id: null`)

#### Equipment Cost Normalization
```json
// Current
{
  "cost": "15 gp",
  "weight": "3 lb"
}

// Improved
{
  "cost": {
    "amount": 15,
    "currency": "gp",
    "copper_value": 1500  // Normalized for <10gp queries
  },
  "weight": {
    "pounds": 3,
    "encumbrance_category": "standard"
  }
}
```

**Clean up placeholder fields:**
- **Remove** `variant_of`, `is_magic`, `rarity` from equipment.schema.json
- **Reason:** Mixing concerns - equipment = mundane, magic_items = magical
- Relationship handled via new `magical_variants` ↔ `base_item_id` cross-links

**Why now:** Tests structure flexibility before 5.2.1 pricing changes

#### Equipment Damage Structuring
```json
// Current
{
  "damage": "1d8 slashing",
  "properties": "versatile (1d10)"
}

// Improved
{
  "damage": {
    "dice": "1d8",
    "type": "slashing",
    "type_id": "damage_type:slashing"
  },
  "properties": [
    {
      "name": "versatile",
      "property_id": "weapon_property:versatile",
      "value": "1d10"
    }
  ]
}
```

#### Implementation
- **Files:** `postprocess_equipment.py`, `equipment.schema.json`
- **Effort:** 1 week (affects 106 items, need careful migration)

**Deliverable:** Equipment queryable by structured properties + magic items linked to bases

**Total v0.19 Effort:** ~1.5 weeks (equipment normalization 1 week + magic item linking 0.5 week)

---

### v0.20.0 - Atomic Reference Datasets (1 week)
**Goal:** Extract hidden reference data from tables/text into standalone datasets

These are **cross-version stable** - same in 5.1, 5.2.1, and likely OGL.

#### Create New Datasets

1. **ability_scores.json** (6 items)
   ```json
   {
     "items": [
       {
         "id": "ability:strength",
         "simple_name": "strength",
         "abbreviation": "STR",
         "name": "Strength",
         "description": "Strength measures bodily power...",
         "skills": ["skill:athletics"],
         "page": 175
       }
     ]
   }
   ```
   - **Source:** Extract from `tables.json` ability_scores_and_modifiers + text
   - **Effort:** 2-3 hours

2. **skills.json** (18 items)
   ```json
   {
     "items": [
       {
         "id": "skill:perception",
         "simple_name": "perception",
         "name": "Perception",
         "ability": "wisdom",
         "ability_id": "ability:wisdom",
         "description": "Your Wisdom (Perception) check...",
         "page": 178
       }
     ]
   }
   ```
   - **Source:** Parse "Using Ability Scores" chapter
   - **Effort:** 4-6 hours

3. **damage_types.json** (13 items)
   ```json
   {
     "items": [
       {
         "id": "damage_type:fire",
         "simple_name": "fire",
         "name": "Fire",
         "description": "Red dragons breathe fire...",
         "page": 196
       }
     ]
   }
   ```
   - **Source:** Parse "Damage Types" section
   - **Effort:** 2-3 hours

4. **weapon_properties.json** (10 items)
   ```json
   {
     "items": [
       {
         "id": "weapon_property:versatile",
         "simple_name": "versatile",
         "name": "Versatile",
         "description": "This weapon can be used with one or two hands...",
         "page": 147
       }
     ]
   }
   ```
   - **Source:** Parse equipment chapter
   - **Effort:** 2-3 hours

**Deliverable:** 4 new atomic datasets, update equipment to reference them

---

### v0.21.0 - Computed Fields (3 days)
**Goal:** Add derivable stats that apps shouldn't recalculate

#### Ability Modifiers
```python
# In postprocess_monsters.py
def add_ability_modifiers(entity):
    """Add computed modifiers to ability_scores"""
    for ability, score in entity["ability_scores"].items():
        entity["ability_scores"][f"{ability}_modifier"] = (score - 10) // 2
```

```json
// Result
{
  "ability_scores": {
    "strength": 18,
    "strength_modifier": 4,  // ← Add this
    "dexterity": 14,
    "dexterity_modifier": 2
  }
}
```

**Apply to:** monsters, classes
**Effort:** 2 hours (simple math, schema updates)

#### Proficiency Bonuses (Monsters)
```json
{
  "challenge_rating": "10",
  "proficiency_bonus": 4  // ← Lookup from CR table
}
```

**Effort:** 1 hour (CR → prof bonus is fixed table)

**Deliverable:** Apps don't need to recalculate basic stats

---

### v0.22.0 - Enhanced Indexes + Validation + Quality (1.5 weeks)
**Goal:** Cross-dataset queries, reference integrity checks, AND close quality gaps from audit

#### Extend index.json
```json
{
  "cross_references": {
    "spells_inflicting_condition": {
      "condition:paralyzed": ["spell:hold_person", "spell:hold_monster"]
    },
    "monsters_casting_spell": {
      "spell:darkness": ["monster:drow", "monster:drow_priestess"]
    },
    "items_granting_spell": {
      "spell:fireball": ["magic_item:wand_of_fireballs"]
    },
    "features_by_lineage": {
      "lineage:dwarf": ["feature:darkvision", "feature:dwarven_resilience"]
    }
  }
}
```

**Implementation:**
- Extend `indexer.py` to build reverse lookups
- **Effort:** 4-6 hours

#### Add Validation Suite
```python
# validate_references.py (NEW)
def validate_cross_references(datasets, index):
    """Ensure all ID references resolve"""
    errors = []

    # Check monster innate spells
    for monster in datasets['monsters']['items']:
        if spells := monster.get('innate_spellcasting', {}).get('spells', []):
            for spell_ref in spells:
                spell_id = spell_ref['spell_id']
                if spell_id not in datasets['spells']['by_id']:
                    errors.append(f"Dangling spell ref in {monster['id']}: {spell_id}")

    # Check class features
    for cls in datasets['classes']['items']:
        for feature_id in cls.get('features', []):
            if feature_id not in datasets['features']['by_id']:
                errors.append(f"Dangling feature ref in {cls['id']}: {feature_id}")

    return errors
```

**Tests:**
- No dangling IDs
- All indexes are complete (every entity appears where expected)
- Cross-references are bidirectional (if A→B, then B's index includes A)

**Effort:** 2-3 days

#### Test Coverage Improvements (from Gemini audit)

**Goal:** Reach 85%+ coverage, close critical gaps

**Priority modules** (currently 0-19% coverage):
- `parse_madness.py` → 85%+
- `parse_poisons.py` → 85%+
- `table_indexer.py` → 90%+ (critical infrastructure)

**New test files to add:**
```python
# tests/test_parse_madness.py (NEW)
def test_madness_parsing():
    """Ensure madness effects are captured correctly"""

# tests/test_parse_poisons.py (NEW)
def test_poison_parsing():
    """Ensure poison effects are captured correctly"""

# tests/test_table_indexer.py (expand coverage to 90%)
def test_indexer_handles_all_categories():
    """Test indexer against all table categories"""
```

**Golden file tests:**
- Add spell description regression test (prevent v0.17.1 bug)
- Add full madness dataset golden test
- Add full poisons dataset golden test

**Effort:** 2-3 days

#### Type Safety Enforcement (from Gemini audit)

**Goal:** Fix overly permissive type checking

**Current issue:** `disallow_untyped_defs = false` masks 21 untyped functions

**Tasks:**
1. Set `disallow_untyped_defs = true` in pyproject.toml
2. Add type hints to 21 functions flagged by mypy
3. Remove `continue-on-error: true` from CI mypy step

**Effort:** 1 day

**Deliverable:** Validated cross-references + 85%+ test coverage + strict type checking

---

### v0.23.0 - Terminology System (3 days)
**Goal:** Prepare for race→species transition in 5.2.1

#### Create terminology.json
```json
{
  "_meta": {
    "schema_version": "1.0.0"
  },
  "mappings": {
    "character_origin": {
      "canonical": "lineage",
      "by_version": {
        "dnd_5.1": "race",
        "dnd_5.2.1": "species"
      },
      "aliases": ["ancestry", "heritage", "race", "species"]
    },
    "saving_throw_bonus": {
      "canonical": "proficiency_bonus",
      "by_version": {
        "dnd_5.1": "proficiency bonus",
        "dnd_5.2.1": "proficiency bonus"
      },
      "aliases": ["prof_bonus", "proficiency"]
    },
    "character_advancement": {
      "canonical": "experience_points",
      "by_version": {
        "dnd_5.1": "experience points",
        "dnd_5.2.1": "experience points"
      },
      "aliases": ["XP", "exp"]
    }
  }
}
```

**Benefits:**
- Consuming apps can query by any term
- Documents which versions use which terminology
- Makes 5.2.1 integration smoother

**Implementation:**
- Create extraction script
- Update indexer to support alias lookups
- **Effort:** 2-3 days

**Deliverable:** Multi-version terminology layer

---

### v0.24.0 - Documentation & Polish (1 week)

#### 1. DATA_DICTIONARY.md
Comprehensive reference covering:
- All 15 datasets (11 current + 4 new atomic)
- Cross-reference patterns with examples
- Query patterns (by_cr, by_level, etc.)
- ID conventions
- Schema evolution policy

#### 2. Inline Documentation (from Gemini audit)

**Goal:** Add comprehensive docstrings to critical modules

**Priority functions** (currently undocumented):
- `src/srd_builder/build.py`: `build()`, `_write_datasets()`
- All public API functions in parse/extract modules
- Complex internal functions

**Follow PEP 257 conventions:**
```python
def build(ruleset: str, output_dir: Path) -> BuildReport:
    """
    Build complete dataset bundle for specified ruleset.

    Args:
        ruleset: Ruleset identifier (e.g., 'srd_5_1')
        output_dir: Directory for generated datasets

    Returns:
        BuildReport containing metadata about generated files

    Raises:
        ValueError: If ruleset not found
        ExtractionError: If PDF extraction fails
    """
```

**Effort:** 1-2 days (integrated with other documentation work)

#### 3. Integration Examples

**Python:**
```python
# examples/load_and_query.py
import json
from pathlib import Path

# Load datasets
data_dir = Path("dist/srd_5_1")
monsters = json.loads((data_dir / "monsters.json").read_text())
spells = json.loads((data_dir / "spells.json").read_text())
index = json.loads((data_dir / "index.json").read_text())

# Query: All CR 10 monsters
cr10 = [m for m in monsters['items'] if m['challenge_rating'] == '10']

# Query: Monsters that cast Darkness
darkness_casters = index['cross_references']['monsters_casting_spell']['spell:darkness']
monsters_list = [m for m in monsters['items'] if m['id'] in darkness_casters]

# Query: All wizard spells
wizard_spells = index['spells']['by_class']['wizard']
```

**JavaScript:**
```javascript
// examples/load_and_query.js
const fs = require('fs');

const monsters = JSON.parse(fs.readFileSync('dist/srd_5_1/monsters.json'));
const index = JSON.parse(fs.readFileSync('dist/srd_5_1/index.json'));

// Query: Fire-resistant creatures
const fireResistant = monsters.items.filter(m =>
  m.damage_resistances?.some(r => r.type_id === 'damage_type:fire')
);
```

#### 3. Migration Guide
For v0.17 → v1.0 schema changes:
- Equipment cost structure changes
- New cross-reference fields
- Deprecated fields (if any)

#### 4. Reddit Announcement Draft
**Title:** "SRD-Builder v1.0: Reproducible D&D 5e SRD Datasets with Full Cross-References"

**Content:**
> I've built a tool that extracts D&D 5e SRD content into validated JSON datasets with source provenance. Every stat block traces back to SRD page numbers.
>
> **Features:**
> - 15 datasets (monsters, spells, equipment, classes, etc.)
> - Navigable cross-references (spells→conditions, monsters→innate spells)
> - Offline-first (no API server needed)
> - Deterministic builds (same PDF → same JSON hash)
> - MIT licensed code, CC-BY 4.0 data
>
> **Use cases:**
> - Solo gaming engines
> - VTT integrations
> - Academic research
> - Legal-compliant reference apps
>
> **Repo:** github.com/wolftales/srd-builder
>
> Feedback welcome! Planning to add 5.2.1 and Pathfinder next.

**Deliverable:** Complete documentation suite

---

### v1.0.0 - Release 🚀

**Checklist:**
- [ ] All 15 datasets extracted and validated
- [ ] Cross-references working and tested
- [ ] Indexes complete with reverse lookups
- [ ] Schemas up to date (v2.0.0)
- [ ] Documentation complete
- [ ] Integration examples tested
- [ ] Reddit announcement ready
- [ ] GitHub release with assets

**Tag line:** "Complete D&D 5e SRD Foundation with Navigable Cross-References"

**Assets to include in release:**
- `dist/srd_5_1.zip` - Complete dataset bundle
- `schemas/` - All JSON schemas
- `examples/` - Integration code
- `DATA_DICTIONARY.md`

---

## Post-v1.0: The 5.2.1 Test (v1.1.0)

### Goals
1. Extract SRD 5.2.1 using existing pipeline
2. Discover architectural pain points
3. Implement version differentiation strategy
4. Build version comparison tooling

### Expected Discoveries

#### ID Strategy
**Question:** Do IDs need version prefixes?

**Options:**
```
A. Global IDs (current):
   monster:aboleth  // Works if content identical

B. Versioned IDs:
   dnd51:monster:aboleth
   dnd52:monster:aboleth

C. Hybrid:
   monster:aboleth           // Alias to latest
   monster:aboleth@dnd51     // Explicit version
```

**Decision Point:** Can an app load both versions simultaneously?

#### Schema Flexibility
Some 5.2.1 changes might need schema updates:
- New condition (e.g., "Slowed" added)
- Balance changes (spell damage dice)
- Deprecated content (specific monsters removed)

**Test:** Does your schema allow version-specific fields?

```json
{
  "id": "spell:fireball",
  "damage": {
    "dnd_5.1": "8d6",
    "dnd_5.2.1": "7d6"  // Hypothetical nerf
  }
}
```

Or separate files entirely?

#### Terminology Mapping
```json
// terminology.json in action
{
  "character_origin": {
    "canonical": "lineage",
    "by_version": {
      "dnd_5.1": "race",
      "dnd_5.2.1": "species"  // ← Test this
    }
  }
}
```

### Deliverables (v1.1.0)
- [ ] 5.2.1 extracted to `dist/srd_5_2_1/`
- [ ] Version comparison report (what changed)
- [ ] Updated terminology.json with 5.2.1 mappings
- [ ] Decision on ID strategy documented
- [ ] Lessons learned → v2.0 architecture plan

---

## Eventual v2.0: Multi-System Architecture

**Only tackle after 5.2.1 proves what you need.**

Likely includes:
- System abstraction layer
- Version-aware schemas
- Cross-system reference resolution
- Unified query API

**But don't design this now** - let 5.2.1 inform the requirements.

---

## Timeline Summary

| Version | Focus | Duration | Cumulative |
|---------|-------|----------|------------|
| **v0.17.1** | **Critical hotfix (spells + equipment)** | **3-5 days** | **3-5 days** |
| v0.18 | Cross-references + security | 1.5 weeks | 2-2.5 weeks |
| v0.19 | Property normalization + magic links | 1.5 weeks | 3.5-4 weeks |
| v0.20 | Atomic datasets | 1 week | 4.5-5 weeks |
| v0.21 | Computed fields | 3 days | ~5.5 weeks |
| v0.22 | Indexes + validation + quality | 1.5 weeks | ~7 weeks |
| v0.23 | Terminology | 3 days | ~7.5 weeks |
| v0.24 | Documentation + docstrings | 1 week | ~8.5 weeks |
| **v1.0** | **Release** | - | **~8.5 weeks** |
| v1.1 | 5.2.1 extraction | 2 weeks | ~10.5 weeks |

**Target date for v1.0:** ~Late February 2025
**Target date for v1.1 (5.2.1):** ~Mid-March 2025

**CRITICAL:** v0.17.1 is **blocking** - must fix spell/equipment bugs before v0.18

---

## Success Metrics for v1.0

### Completeness
- ✅ All SRD 5.1 content extracted (15 datasets)
- ✅ No dangling cross-references
- ✅ 100% schema compliance

### Usability
- ✅ Can query "all fire-resistant CR 10 creatures" in <3 operations
- ✅ Can find "all spells that inflict paralysis" via index
- ✅ Can trace monster → spell → condition → description

### Quality
- ✅ Deterministic builds (hash-stable)
- ✅ Source provenance for every entry
- ✅ Integration examples work out of the box

### Community
- ✅ Reddit post gets >50 upvotes
- ✅ First external contributor PR
- ✅ Used in at least one external project

---

## Next Actions

### This Week
1. **Review this roadmap** - Adjust priorities if needed
2. **Start v0.18** - Pick easiest win (lineages→features)
3. **Set up project board** - GitHub issues for each task

### This Month (December)
- Complete v0.18 (cross-references)
- Start v0.19 (property normalization)

### January
- Complete v0.19-v0.21
- Heavy testing phase

### February
- v0.22-v0.24 (polish)
- v1.0 release

---

## Appendix: Why This Sequence?

### Why Cross-References First?
**Reason:** Unblocks solo gaming use case immediately. Apps can now traverse spell→condition without string parsing.

### Why Property Normalization Before Atomic Datasets?
**Reason:** Tests schema flexibility with known data (equipment). If this breaks things, you discover it before adding 4 new datasets.

### Why Atomic Datasets Before Indexes?
**Reason:** Indexes need stable IDs to reference. Creating skills.json first means monsters can reference `skill:perception` when you build cross-reference indexes.

### Why Terminology Last (Before Docs)?
**Reason:** It's forward-looking (5.2.1), not blocking v1.0 functionality. But must exist before public release so it's documented.

### Why 5.2.1 After v1.0?
**Reason:** Don't let perfect be enemy of good. Ship v1.0 (5.1 complete), get feedback, THEN tackle multi-version complexity with real-world usage data.

---

## Questions? Concerns?

Before committing to this roadmap, consider:

1. **Is 7 weeks realistic?** (Assumes ~15-20 hrs/week)
2. **Any v0.18 tasks blocking others?** (Should lineages→features come first?)
3. **Do you want to defer property normalization?** (Could push to v1.1 if risky)
4. **Is terminology.json premature?** (Could be v1.1 when 5.2.1 is concrete)

Adjust as needed - this is a plan, not a contract!
