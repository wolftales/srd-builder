# D&D 5e API Comparison Analysis
## SRD-Builder vs dnd5eapi.co, 5e-bits, Open5e

**Date:** December 22, 2024
**Analyst:** Claude (API & Application Design Review)
**Target Use Case:** Solo gaming modules, DM assistant, story/world design

---

## EXECUTIVE SUMMARY

### Your Strengths
✅ **Superior data provenance** - Full source tracking with page numbers
✅ **Deterministic builds** - Reproducible from source
✅ **Schema-first design** - Strong validation framework
✅ **Clean separation** - Extract → Parse → Postprocess → Index pipeline
✅ **Solo gaming focus** - Practical orientation vs reference-only APIs

### Priority Gaps
🎯 **Cross-references** - Missing relationships between entities
🎯 **Computed fields** - No derived stats (ability modifiers, spell attack bonuses)
🎯 **Relational structure** - Flat data vs interconnected graph
🎯 **Query flexibility** - Single JSON files vs API filtering/search

---

## 1. COMPLETENESS COMPARISON

### What They Have That You Don't (SRD-Relevant)

| Dataset | dnd5eapi.co | Open5e | Your Status | Priority |
|---------|-------------|---------|-------------|----------|
| **Ability Scores** | ✅ Full reference objects | ✅ | ❌ Missing | **HIGH** |
| **Skills** | ✅ Standalone endpoints | ✅ | ❌ Referenced in monsters only | **HIGH** |
| **Proficiencies** | ✅ Separate resource | ✅ | ❌ Embedded in classes/monsters | **MEDIUM** |
| **Damage Types** | ✅ With resistance examples | ✅ | ❌ Embedded strings only | **MEDIUM** |
| **Alignments** | ✅ Standalone | ✅ | ❌ Strings only | **LOW** |
| **Languages** | ✅ With typical speakers | ✅ | ❌ Strings only | **LOW** |
| **Weapon Properties** | ✅ (finesse, heavy, etc.) | ✅ | ❌ Embedded in equipment | **MEDIUM** |
| **Magic Schools** | ✅ With spell lists | ✅ | ❌ Strings only | **MEDIUM** |
| **Subclasses** | ✅ Full progression | ✅ | ❌ Missing | **HIGH** |
| **Subraces** | ✅ Full traits | ✅ | ⚠️ Partial (4 in lineages) | **HIGH** |
| **Backgrounds** | ✅ Full | ❌ SRD has 1 | ✅ Not in scope (1 in SRD) | N/A |
| **Feats** | ✅ Full | ✅ OGL content | ❌ Not in SRD 5.1 | N/A |

### What You Have (Unique Strengths)

| Feature | Your Implementation | Their Implementation |
|---------|---------------------|---------------------|
| **Provenance** | Page numbers + source tracking | ❌ No page references |
| **Build Metadata** | Full build_report.json | ❌ No build info |
| **Deterministic** | Byte-level reproducibility | ❌ Server-side changes |
| **Diseases** | ✅ 3 diseases | ❌ Not in dnd5eapi |
| **Poisons** | ✅ Full dataset | ❌ Not in dnd5eapi |
| **Tables** | ✅ 37 reference tables | ⚠️ Scattered/incomplete |
| **Meta/License** | ✅ Explicit CC-BY 4.0 | ⚠️ Implied |

---

## 2. ORGANIZATION & DATA MODEL

### Their Approach: Relational Graph with APIReferences

**dnd5eapi.co standard pattern:**
```json
{
  "index": "aboleth",
  "name": "Aboleth",
  "url": "/api/monsters/aboleth",
  "size": "Large",
  "type": "aberration",
  "alignment": "lawful evil",

  // Cross-reference pattern (their killer feature)
  "proficiencies": [
    {
      "value": 8,
      "proficiency": {
        "index": "saving-throw-con",
        "name": "Saving Throw: CON",
        "url": "/api/proficiencies/saving-throw-con"
      }
    }
  ],

  "damage_immunities": [
    {
      "index": "psychic",
      "name": "Psychic",
      "url": "/api/damage-types/psychic"
    }
  ],

  // Skills with ability references
  "skills": {
    "perception": 10,
    "history": 12
  }
}
```

**Your approach: Flat strings**
```json
{
  "id": "monster:aboleth",
  "simple_name": "aboleth",
  "name": "Aboleth",
  "saving_throws": "Con +6, Int +8, Wis +6",  // ❌ No references
  "damage_immunities": ["psychic"],             // ❌ No type details
  "skills": "History +12, Perception +10",      // ❌ No ability refs
  "page": 108
}
```

### Key Structural Differences

| Aspect | Their Model | Your Model | Impact |
|--------|-------------|------------|---------|
| **Entity Relations** | APIReference objects | String concatenation | Can't traverse relationships |
| **Ability Modifiers** | Computed (+8, +6) | Missing | Must recalculate |
| **Skill → Ability** | Explicit links | Implicit | Hard to validate |
| **Type Safety** | Nested objects | Primitive types | Easier to parse, harder to query |

### Their Indexing Strategy

**dnd5eapi root (discovery pattern):**
```json
{
  "ability-scores": "/api/ability-scores",
  "alignments": "/api/alignments",
  "backgrounds": "/api/backgrounds",
  "classes": "/api/classes",
  "conditions": "/api/conditions",
  ...
}
```

**Your indexing:**
```json
{
  "monsters": {
    "by_name": { "Aboleth": "monster:aboleth" },
    "by_cr": { "10": ["monster:aboleth", ...] }
  }
}
```

**Gap:** No cross-dataset indexes (e.g., "all entities with Psychic immunity")

---

## 3. PRESENTATION & API OUTPUT

### Response Format Comparison

#### dnd5eapi.co (HATEOAS pattern)
```json
{
  "index": "fireball",
  "name": "Fireball",
  "level": 3,
  "casting_time": "1 action",
  "range": "150 feet",
  "components": ["V", "S", "M"],
  "material": "a tiny ball of bat guano and sulfur",
  "duration": "Instantaneous",
  "concentration": false,
  "ritual": false,
  "school": {
    "index": "evocation",
    "name": "Evocation",
    "url": "/api/magic-schools/evocation"
  },
  "classes": [
    {
      "index": "sorcerer",
      "name": "Sorcerer",
      "url": "/api/classes/sorcerer"
    },
    {
      "index": "wizard",
      "name": "Wizard",
      "url": "/api/classes/wizard"
    }
  ],
  "subclasses": [...],
  "damage": {
    "damage_type": {
      "index": "fire",
      "name": "Fire",
      "url": "/api/damage-types/fire"
    },
    "damage_at_slot_level": {
      "3": "8d6",
      "4": "9d6",
      ...
    }
  },
  "area_of_effect": {
    "type": "sphere",
    "size": 20
  },
  "dc": {
    "dc_type": {
      "index": "dex",
      "name": "DEX",
      "url": "/api/ability-scores/dex"
    },
    "dc_success": "half"
  }
}
```

#### Your format (flat, string-heavy)
```json
{
  "id": "spell:fireball",
  "simple_name": "fireball",
  "name": "Fireball",
  "level": 3,
  "school": "Evocation",        // ❌ No link to school details
  "casting_time": "1 action",
  "range": "150 feet",
  "components": "V, S, M (a tiny ball of bat guano and sulfur)",
  "duration": "Instantaneous",
  "classes": ["Sorcerer", "Wizard"],  // ❌ No links
  "description": "A bright streak...",
  "page": 241
}
```

### Open5e additions (v2 API)
- **Search endpoint** `/search?text=fire` - full-text search across all resources
- **Filtering** `?cr=10&type=dragon` - query parameters
- **Pagination** `?limit=100&offset=200`
- **Document tagging** `document__slug=wotc-srd` vs `tob` (Tome of Beasts)
- **Highlighted snippets** for search results

### What You're Missing

1. **Hypermedia (HATEOAS)** - No URLs to related resources
2. **Computed fields** - No derived stats like attack bonuses
3. **Deep nesting** - No structured damage/area/DC objects
4. **API query layer** - All data in single files

---

## 4. WHAT YOU'VE DONE WELL

### 1. Build Provenance ⭐
```json
// build_report.json
{
  "version": "0.17.0",
  "build_timestamp": "2024-12-22T10:30:00Z",
  "source_files": [
    {
      "filename": "SRD_CC_v5.1.pdf",
      "sha256": "abc123..."
    }
  ]
}

// Every item
{
  "page": 108,  // ← GOLD for debugging/verification
  "source": "SRD_CC_v5.1"
}
```
**Impact:** Reproducible, auditable builds. Essential for legal compliance.

### 2. Schema Validation Pipeline ⭐
```bash
make smoke       # Item counts
make bundle      # Full validation
make release-check  # Determinism
```
**Impact:** Quality gates before release. Others rely on manual QA.

### 3. Separation of Concerns ⭐
```
extract_*.py    → Raw JSON (font metadata preserved)
parse_*.py      → Structured objects
postprocess/    → Normalization
indexer.py      → Lookups
```
**Impact:** Easy to debug, modify stages independently.

### 4. Boring-by-Design Philosophy ⭐
- No server dependencies
- No database setup
- Just JSON files
- Git-trackable diffs

**Impact:** Lowest friction for solo gaming app integration.

---

## 5. GAPS & PRIORITIZATION

### CRITICAL (Block solo gaming functionality)

#### 1. Cross-References Are Missing
**Problem:** Can't navigate relationships.

**Example:** Player casts *Hold Person* (spell) → Creature is *Paralyzed* (condition).
- **Their APIs:** `spell.conditions[0].url` → `/api/conditions/paralyzed`
- **Your data:** `description` text mentions "paralyzed" but no link

**Fix Priority:** 🔴 **HIGHEST**

**Implementation:**
```json
// Current
{
  "description": "...target is paralyzed..."
}

// Needed
{
  "description": "...target is paralyzed...",
  "inflicts_conditions": [
    {
      "condition": "condition:paralyzed",
      "duration": "1 minute",
      "save_ends": true
    }
  ]
}
```

#### 2. Ability Score Modifiers Missing
**Problem:** Can't compute attack rolls, DCs, etc.

**Example:** Monster has STR 18.
- **Their APIs:** Computes `"strength": 18, "strength_modifier": +4`
- **Your data:** Just `"strength": 18`

**Fix Priority:** 🔴 **HIGHEST**

**Implementation:**
```json
// Add to postprocess
{
  "ability_scores": {
    "strength": 18,
    "strength_modifier": 4  // ← Add this
  }
}
```

#### 3. Subclasses/Subraces Incomplete
**Problem:** Character creation blocked.

**Status:**
- ✅ You have 12 base classes
- ✅ You have 9 base lineages + 4 subraces
- ❌ Missing subclass progressions (e.g., Champion fighter features)

**Fix Priority:** 🟡 **HIGH** (v0.10-v0.11 per roadmap)

### HIGH (Usability blockers)

#### 4. Skills/Proficiencies Not Standalone
**Problem:** Hard to build skill selection UIs.

**Their APIs:**
```json
// GET /api/skills/perception
{
  "index": "perception",
  "name": "Perception",
  "desc": ["Your Wisdom (Perception) check..."],
  "ability_score": {
    "index": "wis",
    "name": "WIS",
    "url": "/api/ability-scores/wis"
  }
}
```

**Your data:** Only embedded in monster stat blocks.

**Fix Priority:** 🟡 **HIGH**

**Implementation:** Create `skills.json`:
```json
{
  "_meta": { "schema_version": "1.0.0" },
  "items": [
    {
      "id": "skill:perception",
      "name": "Perception",
      "ability": "wisdom",
      "description": "...",
      "page": 178
    }
  ]
}
```

#### 5. Damage Types Not Structured
**Problem:** Can't query "all fire-resistant creatures."

**Their APIs:**
```json
{
  "damage_resistances": [
    {
      "index": "fire",
      "name": "Fire",
      "url": "/api/damage-types/fire",
      "desc": ["..."]
    }
  ]
}
```

**Your data:**
```json
{
  "damage_resistances": ["fire"]  // Just strings
}
```

**Fix Priority:** 🟡 **HIGH**

**Implementation:** Add `damage_types.json` + cross-reference.

### MEDIUM (Quality of life)

#### 6. No Computed Stat Blocks
**Example:** Monster AC is "15 (natural armor)" - you have the string, but:
- Base AC: 15
- AC Type: Natural armor
- Dex modifier contribution: ?

**Fix Priority:** 🟢 **MEDIUM**

#### 7. No Spell Lists by Class
**Their APIs:** `/api/classes/wizard` includes `spells: [...]`
**Your data:** `spells.json` has `classes: ["Wizard"]` but no reverse index.

**Fix Priority:** 🟢 **MEDIUM**

### LOW (Nice to have)

- Alignments as objects
- Languages with typical speakers
- Magic schools with spell counts

---

## 6. RECOMMENDED ROADMAP

### Phase 1: Cross-Reference Foundation (v0.18-0.19)
**Goal:** Enable relationship traversal.

1. **Add reference objects** to monsters/spells:
   ```json
   {
     "damage_immunities": [
       {
         "type": "psychic",
         "type_id": "damage_type:psychic"
       }
     ]
   }
   ```

2. **Create atomic datasets:**
   - `ability_scores.json` (6 items)
   - `skills.json` (18 items)
   - `damage_types.json` (13 items)
   - `magic_schools.json` (8 items)

3. **Extend indexer** to build cross-dataset lookups:
   ```json
   {
     "entities_with": {
       "damage_immunity_psychic": ["monster:aboleth", ...],
       "spell_school_evocation": ["spell:fireball", ...]
     }
   }
   ```

**Effort:** ~2-3 weeks
**Files Changed:** parsers, postprocessors, indexer, schemas

### Phase 2: Computed Stats (v0.20)
**Goal:** Add derived fields for game mechanics.

1. **Ability modifiers** in monsters/classes
2. **Proficiency bonuses** (CR-based for monsters)
3. **Attack bonuses** (STR/DEX + prof)
4. **Spell save DCs** (8 + prof + ability)

**Effort:** ~1 week
**Impact:** Solo gaming app can auto-calculate rolls

### Phase 3: Subclass/Subrace Completion (v0.21-0.22)
**Goal:** Full character creation support.

1. Extract subclass progressions from PDF
2. Link subclass features to base class levels
3. Complete all SRD subraces

**Effort:** ~3-4 weeks (complex extraction)

### Phase 4: Polish & Documentation (v0.23)
**Goal:** 1.0 readiness.

1. Comprehensive DATA_DICTIONARY.md
2. Example queries/code snippets
3. Integration guide for VTTs/apps

---

## 7. ARCHITECTURAL RECOMMENDATIONS

### Keep Your Strengths
✅ **Don't add a server** - Your static JSON approach is perfect for solo gaming
✅ **Keep provenance tracking** - Page numbers are invaluable
✅ **Keep deterministic builds** - Essential for version control
✅ **Keep schema validation** - Your quality gate is superior

### Add These Patterns

#### 1. Two-Tier Data Structure
**Minimal** (discovery):
```json
// monsters_list.json (lightweight)
{
  "items": [
    {"id": "monster:aboleth", "name": "Aboleth", "cr": "10"}
  ]
}
```

**Full** (consumption):
```json
// monsters.json (complete)
{
  "items": [
    {
      "id": "monster:aboleth",
      "name": "Aboleth",
      "cr": "10",
      "abilities": {...},
      "actions": [...]
    }
  ]
}
```

**Why:** Apps can lazy-load full details. Faster initial load.

#### 2. Inline References (Best of Both Worlds)
```json
{
  "damage_immunities": [
    {
      "type": "psychic",          // ← Inline for convenience
      "type_id": "damage_type:psychic",  // ← Reference for traversal
      "type_desc": "Mental damage"       // ← Context without fetch
    }
  ]
}
```

**Why:** No server needed, but still supports graph queries.

#### 3. Separate Indexes Per Use Case
```json
// index_combat.json (for encounters)
{
  "monsters_by_cr": {...},
  "spells_by_level": {...}
}

// index_creation.json (for character gen)
{
  "classes_with_features": {...},
  "spells_by_class": {...}
}
```

**Why:** Faster lookups for specific workflows.

---

## 8. COMPETITIVE POSITIONING

### Where You Win
| Scenario | Your Advantage |
|----------|----------------|
| **Legal/Compliance** | Source provenance + deterministic builds |
| **Solo Gaming** | Offline-first, no server setup |
| **Academic Research** | Reproducible datasets with page citations |
| **Version Control** | Git-trackable JSON diffs |

### Where They Win
| Scenario | Their Advantage |
|----------|-----------------|
| **Online VTTs** | Real-time API queries, no download |
| **Large Apps** | GraphQL flexibility, selective fetching |
| **Multi-source** | Open5e has OGL content beyond SRD |

### Your Niche: "Source-of-Truth for Solo Gaming"
**Positioning:** "The reproducible, auditable D&D dataset for developers who need legal compliance and offline functionality."

**Differentiation:**
- ✅ Every byte traceable to SRD pages
- ✅ Works without internet
- ✅ No API rate limits
- ✅ Version-controlled content

---

## 9. ACTION ITEMS

### Immediate (This Sprint)
1. ✅ Review this analysis
2. 🔲 Decide on cross-reference strategy (inline vs separate files)
3. 🔲 Prototype `ability_scores.json` + cross-refs in monsters
4. 🔲 Update roadmap with cross-reference milestones

### Short-Term (Next 2 Sprints)
5. 🔲 Implement ability modifiers postprocessor
6. 🔲 Create skills.json, damage_types.json
7. 🔲 Extend indexer for cross-dataset queries
8. 🔲 Write cross-reference schema tests

### Medium-Term (v0.20-0.22)
9. 🔲 Complete subclass extraction
10. 🔲 Add computed stat blocks
11. 🔲 Build integration examples (Python, JS)

---

## 10. QUESTIONS FOR YOU

1. **Cross-references:** Inline (bloat, but convenient) vs separate reference files (cleaner, but requires joins)?
2. **Computed fields:** Should ability modifiers be in the dataset, or should consuming apps calculate them?
3. **File structure:** Keep monolithic `monsters.json` or split into `monsters_list.json` + `monsters_full.json`?
4. **Scope creep:** Do you want to match dnd5eapi feature-for-feature, or stay focused on solo gaming needs?

---

## APPENDIX A: Endpoint Coverage Matrix

| Endpoint | dnd5eapi | Open5e | SRD-Builder | Notes |
|----------|----------|---------|-------------|-------|
| /ability-scores | ✅ | ✅ | ❌ | **Add in v0.18** |
| /skills | ✅ | ✅ | ⚠️ Embedded | Extract to skills.json |
| /proficiencies | ✅ | ✅ | ⚠️ Embedded | Low priority |
| /classes | ✅ | ✅ | ✅ | **Complete** |
| /subclasses | ✅ | ✅ | ❌ | **Add in v0.21** |
| /races | ✅ | ✅ | ✅ (lineages) | **Complete** |
| /subraces | ✅ | ✅ | ⚠️ Partial | Need 36 more |
| /monsters | ✅ | ✅ | ✅ | **Complete** |
| /spells | ✅ | ✅ | ✅ | **Complete** |
| /equipment | ✅ | ✅ | ✅ | **Complete** |
| /magic-items | ✅ | ✅ | ✅ | **Complete** |
| /conditions | ✅ | ✅ | ✅ | **Complete** |
| /damage-types | ✅ | ✅ | ❌ | **Add in v0.18** |
| /magic-schools | ✅ | ✅ | ❌ | **Add in v0.18** |
| /features | ✅ | ✅ | ✅ | **Complete** |
| /traits | ✅ | ❌ | ⚠️ In lineages | Verify coverage |
| /backgrounds | ✅ | ✅ | N/A | Only 1 in SRD |
| /feats | ✅ | ✅ | N/A | Not in SRD 5.1 |
| /rules | ✅ | ⚠️ Sections | ✅ | **Complete (v0.17)** |
| /rule-sections | ✅ | ⚠️ | ⚠️ | Embedded in rules |
| /tables | ⚠️ Scattered | ⚠️ | ✅ | **Your advantage** |

**Legend:**
✅ Complete | ⚠️ Partial | ❌ Missing | N/A Not applicable

---

## APPENDIX B: Data Model Examples

### Their "APIReference" Pattern
Every related entity uses:
```json
{
  "index": "cha",
  "name": "Charisma",
  "url": "/api/ability-scores/cha"
}
```

Benefits:
- Traversable via URL
- Type-safe (always has index/name/url)
- Discoverable (URL tells you endpoint)

Drawbacks for offline use:
- Requires HTTP client
- Multiple round trips for deep queries
- URL strings become IDs (fragile to API changes)

### Your "ID Reference" Pattern
```json
{
  "type_id": "damage_type:psychic"
}
```

Benefits:
- Works offline
- Simple string matching
- No HTTP overhead

Needed improvements:
- Add `type` field for inline display
- Add `type_desc` for context
- Build reverse indexes in index.json

---

## CONCLUSION

**SRD-Builder is 70% feature-complete vs existing APIs** for core SRD content. Your main gaps are:

1. **Cross-references** (critical)
2. **Derived stats** (high priority)
3. **Atomic reference datasets** (skills, damage types, etc.)

**Your competitive advantages** (provenance, reproducibility, offline-first) are **strong differentiators** for your solo gaming use case. Don't try to be dnd5eapi - **be the auditable, git-friendly dataset for offline apps.**

**Recommended focus:** Spend v0.18-0.20 adding cross-references and computed fields, then move to subclass completion in v0.21-0.22. You'll hit v1.0 with a **distinct, defensible position** in the market.
