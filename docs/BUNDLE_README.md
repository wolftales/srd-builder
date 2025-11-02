# SRD 5.1 Dataset Bundle

**Version:** srd-builder v0.6.0
**Schema Version:** 1.3.0
**Generated:** November 1, 2025
**Source:** System Reference Document 5.1 (SRD_CC_v5.1)

---

## What's Included

Machine-readable D&D 5e SRD data extracted from official PDF:

- **296 Monsters** - Full stat blocks (schema v1.2.0)
- **114 Equipment Items** - Weapons, armor, gear (schema v1.2.0)
- **Spells** - Spell data with structured casting/effects (schema v1.3.0)
- **Search Index** - Pre-built lookups (monsters, equipment, spells)

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
├── monsters.json          # 296 creature stat blocks
├── equipment.json         # 114 items
├── spells.json            # Spell data
├── index.json             # Search index (monsters, equipment, spells)
├── meta.json              # Dataset catalog & license
├── README.md              # This file
├── build_report.json      # Build process metadata
├── schemas/
│   ├── monster.schema.json
│   ├── equipment.schema.json
│   └── spell.schema.json
└── docs/
    ├── SCHEMAS.md         # Schema design & versioning
    └── DATA_DICTIONARY.md # Field reference & SRD mappings
```

---

## Index Structure

The `index.json` file provides pre-built search indexes for all datasets:

```json
{
  "monsters": {
    "by_name": {"aboleth": "monster:aboleth", ...},
    "by_cr": {"0": [...], "1": [...], ...},
    "by_type": {"dragon": [...], "undead": [...], ...},
    "by_size": {"Medium": [...], "Large": [...], ...}
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
  "entities": {
    "monsters": {"monster:aboleth": {"type": "monster", "file": "monsters.json", "name": "Aboleth"}, ...},
    "equipment": {"item:longsword": {"type": "equipment", "file": "equipment.json", "name": "Longsword"}, ...},
    "spells": {"spell:fireball": {"type": "spell", "file": "spells.json", "name": "Fireball"}, ...}
  },
  "stats": {
    "total_monsters": 296,
    "total_equipment": 111,
    "total_spells": 0,
    "total_entities": 407,
    ...
  }
}
```

**Usage:**
- Look up monsters by CR: `index.monsters.by_cr["5"]` → list of CR 5 monster IDs
- Find all concentration spells: `index.spells.by_concentration["true"]`
- Get entity metadata: `index.entities.monsters["monster:aboleth"]` → type, file, name

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

- **Namespaced IDs:** `monster:aboleth`, `item:longsword`, `spell:fireball`
- **Structured data:** AC, HP, speeds, casting as objects (not strings)
- **Normalized names:** `simple_name` for search/indexing
- **Pre-built indexes:** Fast lookups by CR, category, level, etc.
- **Entity directory:** Nested by type (monsters/equipment/spells)
- **Schema validation:** All data validates against JSON Schema Draft 2020-12

```bash
jsonschema -i monsters.json schemas/monster.schema.json
```

---

## License & Attribution

**License:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

**Required Attribution:**
> This work includes material taken from the System Reference Document 5.1 ("SRD 5.1") by Wizards of the Coast LLC. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License.

**Conversion:** [srd-builder](https://github.com/wolftales/srd-builder) v0.6.0

Full license in `meta.json`.
