# SRD 5.1 Dataset Bundle

**Version:** srd-builder v0.13.0
**Schema Version:** 1.3.0
**Generated:** November 9, 2025
**Source:** System Reference Document 5.1 (SRD_CC_v5.1)

---

## What's Included

Machine-readable D&D 5e SRD data extracted from official PDF:

- **317 Creatures** - 201 monsters + 95 misc creatures (MM-A) + 21 NPCs (MM-B) - Full stat blocks (schema v1.3.0)
- **106 Equipment Items** - Weapons, armor, gear (schema v1.3.0)
- **319 Spells** - Spell data with structured casting/effects (schema v1.3.0)
- **23 Tables** - Reference tables including 12 class progression tables (schema v1.3.0)
- **13 Lineages** - Character lineages (formerly races) with traits, abilities, subraces (schema v1.3.0)
- **12 Classes** - Character classes with progression, features, proficiencies (schema v1.3.0)
- **Search Index** - Pre-built lookups with alias support (all datasets)
- **Alias System** - Terminology mappings (races→lineages) and entity-level search aliases

---

## Quick Start

```javascript
// Monsters
const monsters = require('./monsters.json');
const dragon = monsters.items.find(m => m.simple_name === 'adult_red_dragon');
console.log(dragon.challenge_rating);  // 17

// Spells
const spells = require('./spells.json');
const fireball = spells.items.find(s => s.simple_name === 'fireball');
console.log(fireball.level);  // 3
console.log(fireball.effects.damage);  // {dice: "8d6", type: "fire"}
```

```python
import json

# Monsters
with open('monsters.json') as f:
    monsters = json.load(f)['items']
dragon = next(m for m in monsters if m['id'] == 'monster:adult_red_dragon')

# Spells
with open('spells.json') as f:
    spells = json.load(f)['items']
fireball = next(s for s in spells if s['id'] == 'spell:fireball')
print(fireball['effects']['damage'])  # {'dice': '8d6', 'type': 'fire'}
```

---

## Bundle Contents

```
srd_5_1/
├── monsters.json          # 317 creature stat blocks (201 monsters + 95 creatures + 21 NPCs)
├── equipment.json         # 106 items
├── spells.json            # 319 spells
├── tables.json            # 23 reference tables (12 class progression + 11 reference)
├── lineages.json          # 13 character lineages (9 base + 4 subraces)
├── classes.json           # 12 character classes
├── index.json             # Search index with alias support
├── meta.json              # Dataset catalog & license
├── README.md              # This file
├── build_report.json      # Build process metadata
├── schemas/
│   ├── monster.schema.json
│   ├── equipment.schema.json
│   ├── spell.schema.json
│   ├── table.schema.json
│   ├── lineage.schema.json
│   └── class.schema.json
└── docs/
    ├── SCHEMAS.md         # Schema design & versioning
    └── DATA_DICTIONARY.md # Field reference & SRD mappings
```

---

## Index Structure

The `index.json` file provides pre-built search indexes for all datasets:

```json
{
  "aliases": {
    "races": "lineages",
    "race": "lineage"
  },
  "monsters": {
    "by_name": {"aboleth": "monster:aboleth", ...},
    "by_cr": {"0": [...], "1": [...], ...},
    "by_type": {"dragon": [...], "undead": [...], ...},
    "by_size": {"Medium": [...], "Large": [...], ...}
  },
  "creatures": {
    "by_name": {"awakened_shrub": "creature:awakened_shrub", ...},
    "by_cr": {"0": [...], "1": [...], ...},
    "by_type": {"plant": [...], "construct": [...], ...},
    "by_size": {"Tiny": [...], "Small": [...], ...}
  },
  "npcs": {
    "by_name": {"acolyte": "npc:acolyte", ...},
    "by_cr": {"0.125": [...], "0.25": [...], ...},
    "by_type": {"humanoid": [...]},
    "by_size": {"Medium": [...]}
  },
  "equipment": {
    "by_name": {"longsword": "item:longsword", ...},
    "by_category": {"weapon": [...], "armor": [...], ...},
    "by_rarity": {"common": [...], "rare": [...], ...}
  },
  "spells": {
    "by_name": {"fireball": "spell:fireball", ...},
    "by_level": {"0": [...], "1": [...], ...},
    "by_school": {"evocation": [...], "abjuration": [...], ...},
    "by_concentration": {"true": [...], "false": [...]},
    "by_ritual": {"true": [...], "false": [...]}
  },
  "lineages": {
    "by_name": {"dwarf": "lineage:dwarf", "elf": "lineage:elf", ...},
    "by_size": {"Medium": [...], "Small": [...]},
    "by_speed": {"25": [...], "30": [...]}
  },
  "entities": {
    "monsters": {"monster:aboleth": {"type": "monster", "file": "monsters.json", "name": "Aboleth"}, ...},
    "creatures": {"creature:awakened_shrub": {"type": "creature", "file": "monsters.json", "name": "Awakened Shrub"}, ...},
    "npcs": {"npc:acolyte": {"type": "npc", "file": "monsters.json", "name": "Acolyte"}, ...},
    "equipment": {"item:longsword": {"type": "equipment", "file": "equipment.json", "name": "Longsword"}, ...},
    "spells": {"spell:fireball": {"type": "spell", "file": "spells.json", "name": "Fireball"}, ...},
    "lineages": {"lineage:dwarf": {"type": "lineage", "file": "lineages.json", "name": "Dwarf"}, ...}
  },
  "stats": {
    "total_monsters": 201,
    "total_creatures": 95,
    "total_npcs": 21,
    "total_equipment": 114,
    "total_spells": 0,
    "total_lineages": 13,
    "total_entities": 444,
    ...
  }
}
```

**Usage:**
- Look up monsters by CR: `index.monsters.by_cr["5"]` → list of CR 5 monster IDs
- Find all concentration spells: `index.spells.by_concentration["true"]`
- Use legacy terminology: `index[index.aliases["races"]]` → lineages data
- Get entity metadata: `index.entities.monsters["monster:aboleth"]` → type, file, name

---

## Alias Support (v0.8.1)

**Terminology aliases** map historical category names to canonical:

```javascript
// Resolve "races" → "lineages"
const canonical = index.aliases["races"] || "races";  // → "lineages"
index[canonical].by_name["dwarf"]  // → "lineage:dwarf"
```

**Entity aliases** enable partial/alternative search terms:

```javascript
// "tankard" finds "Flask or tankard" (future)
index.equipment.by_name["tankard"]  // → "item:flask_or_tankard"
```

See **SCHEMAS.md** for field details.

---

## Documentation

**Read these files for detailed information:**

- **SCHEMAS.md** - Schema v1.3.0 design, versioning, use cases, evolution history
- **DATA_DICTIONARY.md** - Complete field reference with SRD source mappings
- **meta.json** - License, attribution, file manifest
- **build_report.json** - Extraction statistics
- **schemas/*.json** - JSON Schema validation

---

## Key Features

- **Namespaced IDs:** `monster:aboleth`, `item:longsword`, `spell:fireball`, `lineage:dwarf`
- **Structured data:** AC, HP, speeds, casting, traits as objects (not strings)
- **Normalized names:** `simple_name` for search/indexing
- **Pre-built indexes:** Fast lookups by CR, category, level, size, speed, etc.
- **Entity directory:** Nested by type (monsters/equipment/spells/lineages)
- **Alias support:** Terminology mappings and entity-level search aliases
- **Schema validation:** All data validates against JSON Schema Draft 2020-12

```bash
jsonschema -i monsters.json schemas/monster.schema.json
```

---

## License & Attribution

**License:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

**Required Attribution:**
> This work includes material taken from the System Reference Document 5.1 ("SRD 5.1") by Wizards of the Coast LLC. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License.

**Conversion:** [srd-builder](https://github.com/wolftales/srd-builder) v0.13.0

Full license in `meta.json`.

---

## Known Limitations

**Class Progression Tables (v0.9.8):**

A few minor data quality issues exist in extracted class progression table data:

1. **Monk 6th level:** The feature name "Ki-Empowered Strikes" contains soft hyphen characters (invisible formatting hints present in the source PDF). This does not affect data usability or search.

2. **Rogue 10th level:** The feature cell shows "Ability Score" without "Improvement" - the word "Improvement" appears as continuation text on the next page and is not currently merged. Context makes the full meaning clear (matches other Ability Score Improvement entries at 4th, 8th, 12th, 16th, 19th levels).

These minor issues do not affect the functional use of the data. All class tables contain the correct 20 levels with proper progression values.
