# Schema Versioning & Design Guide

This document describes the schema versioning strategy, evolution patterns, and design principles for srd-builder datasets.

---

## Schema Version: 1.3.0

**Current Version:** `1.3.0`
**Adopted:** v0.6.0 (November 2025)
**Status:** Stable

### What's Included in Schema v1.3.0

All dataset files produced by srd-builder conform to schema version 1.3.0, which includes:

**Core Structure:**
- `_meta` wrapper with dataset metadata
- `items` array containing entity records
- Consistent entity structure: `{id, name, simple_name, page, src, ...}`

**Entity Namespaces:**
- `monster:*` - Monster stat blocks
- `item:*` - Equipment, weapons, armor, gear
- `spell:*` - Spells (v0.6.0)
- `class:*` - Character classes (planned)
- `lineage:*` - Lineages/races (planned)
- `condition:*` - Game conditions (planned)

**Common Patterns:**
- Nested entries with `{name, text}` structure (traits, actions, features)
- Source tracking: `page` and `src` fields on all entities
- Normalized IDs: `simple_name` for search/indexing
- Optional aliases: `aliases: string[]` for alternative search terms (v1.3.0)

---

## Schema File Organization

### Location: `/schemas/`

```
schemas/
├── monster.schema.json       # Monster stat blocks
├── equipment.schema.json     # Equipment/items
├── spell.schema.json         # Spells (v1.3.0)
└── ...
```

### Schema File Structure

Each schema file follows JSON Schema Draft 2020-12 with custom metadata fields:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://wolftales.github.io/srd-builder/schemas/monster.schema.json",
  "version": "1.1.0",
  "last_modified": "2024-11-01",
  "title": "Monster",
  "description": "Schema for D&D 5e monster stat blocks",
  "type": "object",
  "required": ["id", "name", "simple_name", ...],
  "properties": { ... }
}
```

**Version Tracking:**
- `version`: Semantic version (MAJOR.MINOR.PATCH) tracking breaking changes and additions
  - **MAJOR** (1.x.x) - Breaking changes (field renames, type changes, removed fields)
  - **MINOR** (x.1.x) - Non-breaking additions (new optional fields, new enums)
  - **PATCH** (x.x.1) - Documentation/clarification updates (no structural changes)
- `last_modified`: ISO date (YYYY-MM-DD) of last schema file update
  - Updated whenever schema file changes (even documentation-only changes)
  - Helps track incremental updates within same semantic version
  - Useful for identifying fresh additions before next version bump

**Example Evolution:**
- v1.1.0 (2024-10-31) - Added equipment schema with weapon/armor fields
- v1.1.0 (2024-11-01) - Added optional magic item fields (last_modified updated, version unchanged)
- v1.2.0 (future) - Would bump MINOR when those magic fields are actively used in data
- v2.0.0 (future) - Would bump MAJOR if we renamed `simple_name` to `slug` (breaking)

---

## Dataset Metadata: `_meta` Section

Every dataset file includes a `_meta` section documenting its structure:

```json
{
  "_meta": {
    "source": "SRD_CC_v5.1",
    "schema_version": "1.1.0",
    "format": "unified_items_array",
    "entity_count": 296,
    "generated_at": "2025-10-31T05:23:10Z",
    "builder_version": "0.5.0"
  },
  "items": [ ... ]
}
```

### Metadata Fields

| Field | Description | Example |
|-------|-------------|---------|
| `source` | Source document identifier | `"SRD_CC_v5.1"` |
| `schema_version` | Data structure version | `"1.1.0"` |
| `format` | Array structure type | `"unified_items_array"` |
| `entity_count` | Number of items | `296` |
| `generated_at` | Build timestamp | ISO 8601 |
| `builder_version` | srd-builder version | `"0.4.2"` |

---

## Version History

### v1.1.0 (Current) - October 2025

**Context:** Optimized and improved monsters.json structure and parsing process during Week 1 development. Equipment.json adopted these patterns in Week 2.

**Added:**
- Unified `items[]` array format for all entity types
- `simple_name` field for normalized search and indexing
- Namespace prefixes in IDs (`monster:`, `item:`, etc.)
- `_meta` wrapper with schema_version tracking
- Equipment schema with category-specific fields (weapon_category, armor_category, etc.)
- Nested entries pattern with `{name, simple_name, text}` structure
- Structured damage/resistance objects (not strings)

**Changed:**
- Monster abilities → traits (field rename, backwards incompatible)
- Legendary actions split from actions array into separate field
- Damage resistances as structured objects: `{type, qualifier}` instead of strings
- Condition immunities as structured objects
- Challenge rating normalized (fractions → decimals)

**Removed:**
- Legacy directory-based structure (`monsters/`, `spells/`)
- Raw string-based defensive fields

**Datasets conforming to v1.1.0:**
- monsters.json (Week 1, v0.4.0)
- equipment.json (Week 2, v0.5.0)

### v1.0.0 (Initial) - Pre-October 2025

**Context:** Initial schema inherited from MVP/prototype work. Basic extraction with minimal structure.

**Features:**
- Basic monster extraction from PDF
- Directory-based organization (`monsters/`, `spells/` folders)
- Simple string-based fields (no structured objects)
- No namespace prefixes in IDs
- No formal versioning or `_meta` wrappers
- Abilities field (later renamed to traits)

**Known Issues:**
- Inconsistent ID generation
- String-based damage types (hard to parse)
- No cross-dataset patterns
- No validation or schema enforcement

---

## Schema Evolution Principles

### 1. Semantic Versioning

Schemas follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR** - Breaking changes (field removals, type changes, structure changes)
- **MINOR** - Additive changes (new optional fields, new entity types)
- **PATCH** - Clarifications (description updates, constraint fixes)

**Examples:**
- Adding `versatile_damage` to weapons → MINOR bump (1.1.0 → 1.2.0)
- Changing `armor_class` from integer → object → MAJOR bump (1.1.0 → 2.0.0)
- Fixing schema description typo → PATCH bump (1.1.0 → 1.1.1)

### 2. Backwards Compatibility

**Goal:** Consumers using old schemas can still parse new data (within MAJOR version).

**Rules:**
- New fields MUST be optional
- Field types CANNOT change
- Required fields CANNOT be removed
- Enum values can be added but not removed

**Example - Safe Addition:**
```json
// v1.1.0
{
  "id": "item:longsword",
  "name": "Longsword",
  "cost": {"amount": 15, "currency": "gp"}
}

// v1.2.0 - Added optional "rarity" field
{
  "id": "item:longsword",
  "name": "Longsword",
  "cost": {"amount": 15, "currency": "gp"},
  "rarity": "common"  // New field, optional
}
```

### 3. Breaking Changes Require Migration

When MAJOR version changes, provide migration guide.

**Example - Breaking Change (v1.x → v2.0):**
```json
// v1.1.0 - armor_class as integer
{
  "armor_class": 14
}

// v2.0.0 - armor_class as object
{
  "armor_class": {
    "base": 14,
    "dex_bonus": true,
    "max_bonus": 2
  }
}
```

**Migration guide would document:**
- What changed and why
- How to convert old → new
- Compatibility shims if available

---

## Schema Design Patterns

### Pattern 1: Namespace Prefixes

All entity IDs use namespace prefixes to avoid collisions:

```json
{
  "id": "monster:ancient_red_dragon",  // Not just "ancient_red_dragon"
  "id": "item:longsword",               // Not just "longsword"
  "id": "spell:fireball"                // Not just "fireball"
}
```

**Why:** Allows cross-references and prevents ambiguity.

### Pattern 2: Simple Name for Indexing

Every entity has both `name` (display) and `simple_name` (normalized):

```json
{
  "id": "item:chain-mail",
  "name": "Chain Mail",
  "simple_name": "chain_mail"  // Normalized for search/sorting
}
```

**Why:** Consistent indexing regardless of formatting, punctuation, or capitalization.

### Pattern 3: Nested Entries

Actions, traits, features use consistent `{name, text}` structure:

```json
{
  "traits": [
    {
      "name": "Darkvision",
      "simple_name": "darkvision",
      "text": "You can see in dim light within 60 feet..."
    }
  ]
}
```

**Why:** Allows rich structured data while keeping text searchable.

### Pattern 4: Category-Specific Fields

Optional fields based on entity category:

```json
{
  "category": "weapon",
  "weapon_category": "martial",  // Only for weapons
  "weapon_type": "melee",        // Only for weapons
  "damage": { ... }              // Only for weapons
}

{
  "category": "armor",
  "armor_category": "heavy",     // Only for armor
  "armor_class": { ... },        // Only for armor
  "stealth_disadvantage": true   // Only for armor
}
```

**Why:** Keeps schemas focused without forcing all fields on all entities.

### Pattern 5: Structured Over Strings

Prefer structured objects over formatted strings:

**Bad:**
```json
{
  "cost": "15 gp",
  "damage": "1d8 slashing",
  "range": "20/60 ft."
}
```

**Good:**
```json
{
  "cost": {"amount": 15, "currency": "gp"},
  "damage": {"dice": "1d8", "type": "slashing"},
  "range": {"normal": 20, "long": 60}
}
```

**Why:** Enables querying, sorting, validation without string parsing.

---

## Version Declaration Locations

### 1. Schema Files (`/schemas/*.schema.json`)

**Current:** Schema files do NOT include version field (gap to fix)

**Proposed:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://wolftales.github.io/srd-builder/schemas/monster.schema.json",
  "version": "1.1.0",
  "title": "Monster",
  ...
}
```

### 2. Dataset Metadata (`dist/*/data/*.json`)

**Current:** Every dataset file includes `_meta.schema_version`

```json
{
  "_meta": {
    "schema_version": "1.1.0",
    ...
  },
  "items": [ ... ]
}
```

### 3. Build Metadata (`dist/*/meta.json`)

**Current:** Build metadata includes `$schema_version`

```json
{
  "version": "5.1",
  "source": "SRD_CC_v5.1",
  "$schema_version": "1.1.0",
  ...
}
```

---

## Gap Analysis & Recommendations

### Current Gaps

1. ✅ **Schema files now have version field** - Added `"version": "1.1.0"` to all .schema.json files
2. ✅ **Schema documentation exists** - This file (SCHEMAS.md) serves as schema changelog
3. ❌ **No migration guides** - No documentation for breaking changes (needed when v2.0 comes)
4. ❌ **Inconsistent versioning** - Some docs say "v1.1.0", others "1.1.0" (cleanup needed)
5. ❌ **No schema validation of schema_version** - Meta fields not validated against schema version

### Recommendations

1. ✅ **DONE: Added version to schema files** - All schemas now include `"version"` field
2. ✅ **DONE: Created SCHEMAS.md** - This document tracks schema changes and patterns
3. 🔄 **TODO: Document migration paths** - Create MIGRATIONS.md when MAJOR bumps occur (v2.0+)
4. 🔄 **TODO: Standardize version format** - Use "1.1.0" (no "v" prefix) everywhere consistently
5. 🔄 **TODO: Validate schema_version** - Add validation in build.py to ensure schema_version matches schema file version

---

## Spell Schema (v1.3.0)

**Added in:** v0.6.0 (November 2025)
**Schema File:** `schemas/spell.schema.json`
**Version:** 1.3.0

### Design Philosophy

The spell schema uses **structured nested objects** for related fields, following the established pattern from monster actions. This provides:
- Clean root-level organization
- Extensible field grouping
- Type-safe querying
- Future-proof structure

### Core Structure

```json
{
  "id": "spell:fireball",
  "simple_name": "fireball",
  "name": "Fireball",
  "level": 3,
  "school": "evocation",
  "casting": { /* nested object */ },
  "components": { /* nested object */ },
  "effects": { /* optional nested object */ },
  "scaling": { /* optional nested object */ },
  "text": "Full spell description...",
  "page": 241
}
```

### Nested Objects

**`casting` (required):**
```json
{
  "time": "1 action",
  "range": {"kind": "ranged", "value": 150, "unit": "feet"},  // or "self"/"touch"
  "duration": "instantaneous",
  "concentration": false,
  "ritual": false
}
```

**`components` (required):**
```json
{
  "verbal": true,
  "somatic": true,
  "material": true,
  "material_description": "a tiny ball of bat guano and sulfur"  // optional
}
```

**`effects` (optional):**
```json
{
  "damage": {"dice": "8d6", "type": "fire"},
  "save": {"ability": "dexterity", "on_success": "half_damage"},
  "area": {"shape": "sphere", "size": 20, "unit": "feet"},
  "healing": {"dice": "2d8"},  // healing spells
  "attack": {"type": "ranged_spell"},  // attack roll spells
  "conditions": ["blinded", "charmed"]  // condition application
}
```

**`scaling` (optional):**
```json
{
  "type": "slot",  // or "character_level" for cantrips
  "base_level": 3,
  "formula": "+1d6 per slot level above 3rd"  // human-readable
}
```

### Scaling Types

1. **Slot-level scaling** (`"type": "slot"`) - Upcast with higher spell slots
   - Example: Fireball at 4th level does more damage than 3rd

2. **Character-level scaling** (`"type": "character_level"`) - Cantrip scaling
   - Example: Fire Bolt damage increases at 5th, 11th, 17th character level

### Field Enums

**Schools (8):**
`abjuration`, `conjuration`, `divination`, `enchantment`, `evocation`, `illusion`, `necromancy`, `transmutation`

**Damage Types (13):**
`acid`, `bludgeoning`, `cold`, `fire`, `force`, `lightning`, `necrotic`, `piercing`, `poison`, `psychic`, `radiant`, `slashing`, `thunder`

**Abilities (6):**
`strength`, `dexterity`, `constitution`, `intelligence`, `wisdom`, `charisma`

**Area Shapes (5):**
`cone`, `cube`, `cylinder`, `line`, `sphere`

### Design Decisions

1. **Nested objects over flat fields** - Mirrors monster actions structure, enables clean extensibility
2. **Human-readable formula field** - Preserves SRD text, directly displayable to users
3. **Optional effects wrapper** - Not all spells have damage/healing/saves (utility spells)
4. **Flexible range type** - Structured object for numeric ranges, special strings for self/touch/sight

---

## Future Schema Additions

### Planned (v1.4.0+)

- `class.schema.json` - Character classes with features
- `lineage.schema.json` - Lineages/races with traits
- `condition.schema.json` - Game conditions

### Under Consideration (v2.0.0?)

- **Magic items** with base_item references
- **Cross-references** between entities
- **Rich text markup** (markdown, annotations)
- **Computed fields** (e.g., CR-derived stats)
- **Armor class objects** (breaking change from integer)

---

## Consumer Use Cases

Datasets conforming to these schemas are designed for:

### Campaign Tools
- VTT integrations (Roll20, Foundry VTT, Fantasy Grounds)
- Encounter builders and balance calculators
- Initiative trackers with auto-populated stats
- Digital character sheet integrations

### Mobile & Web Apps
- Monster reference apps with offline support
- DM companion tools
- Quick lookup utilities
- Combat assistants

### AI/LLM Applications
- D&D chatbots and virtual DMs
- Rule reference systems
- Content generation tools
- Natural language query interfaces

### Analysis & Research
- Game balance analysis and CR calculations
- Statistical modeling of creature design
- Content exploration and discovery
- Dataset comparisons across editions

---

## Related Documentation

- **ARCHITECTURE.md** - Overall system design
- **ROADMAP.md** - Version timeline and features
- **terminology.aliases.md** - Naming conventions and namespace patterns
- **DATA_DICTIONARY.md** - Field meanings and SRD source mappings
- **INTEGRATION.md** - Consumer guidance (planned)
- **MIGRATIONS.md** - Breaking change guides (planned)

---

## Questions or Issues?

Schema design questions should be documented in:
- **PARKING_LOT.md** - Deferred decisions
- **GitHub Issues** - Active discussions

Schema bugs or gaps should be:
- **Reported as issues** with "schema" label
- **Tested** with fixtures in `tests/fixtures/`
