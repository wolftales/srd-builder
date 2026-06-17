# SRD 5.1 Dataset Bundle

**Builder version:** srd-builder v0.26.2
**Ruleset:** SRD 5.1 (System Reference Document)
**Generated:** (reproducible build)
**Total items:** 1695 across 16 datasets

---

## What's Included

Machine-readable D&D 5e SRD data extracted from the official PDF. Each dataset
ships as a single `*.json` file with a `_meta` block + `items` array.

| Dataset | Items | File | Schema |
|---|---:|---|---|
| Ability Scores | 6 | `ability_scores.json` | v1.0.0 |
| Classes | 12 | `classes.json` | v2.1.0 |
| Conditions | 15 | `conditions.json` | v2.0.0 |
| Damage Types | 13 | `damage_types.json` | v1.0.0 |
| Diseases | 3 | `diseases.json` | v2.0.0 |
| Equipment | 259 | `equipment.json` | v2.1.0 |
| Features | 245 | `features.json` | v3.0.0 |
| Lineages | 13 | `lineages.json` | v2.0.0 |
| Magic Items | 240 | `magic_items.json` | v2.0.0 |
| Monsters | 317 | `monsters.json` | v2.0.0 |
| Poisons | 14 | `poisons.json` | v2.0.0 |
| Rules | 172 | `rules.json` | v2.0.0 |
| Skills | 18 | `skills.json` | v1.0.0 |
| Spells | 319 | `spells.json` | v2.0.0 |
| Tables | 38 | `tables.json` | v2.0.0 |
| Weapon Properties | 11 | `weapon_properties.json` | v1.0.0 |

Plus:

- `meta.json` — bundle metadata (versions, license, page index, inventory)
- `build_report.json` — build provenance (timestamps, builder version)
- `index.json` — pre-built search index with alias support
- `schemas/` — JSON Schema files for all datasets
- `docs/` — `SCHEMAS.md`, `DATA_DICTIONARY.md`

---

## Quick Start

```javascript
// Node.js
const monsters = require('./monsters.json');
const dragon = monsters.items.find(m => m.simple_name === 'adult_red_dragon');
console.log(dragon.challenge_rating);  // 17

const spells = require('./spells.json');
const fireball = spells.items.find(s => s.simple_name === 'fireball');
console.log(fireball.level);  // 3
```

```python
# Python
import json

with open('monsters.json') as f:
    monsters = json.load(f)['items']
dragon = next(m for m in monsters if m['id'] == 'monster:adult_red_dragon')

with open('spells.json') as f:
    spells = json.load(f)['items']
fireball = next(s for s in spells if s['simple_name'] == 'fireball')
```

---

## Schemas

All datasets are validated against JSON Schema files in `schemas/`:

- `ability_score.schema.json` — v1.0.0
- `class.schema.json` — v2.1.0
- `condition.schema.json` — v2.0.0
- `damage_type.schema.json` — v1.0.0
- `disease.schema.json` — v2.0.0
- `equipment.schema.json` — v2.1.0
- `features.schema.json` — v3.0.0
- `lineage.schema.json` — v2.0.0
- `magic_item.schema.json` — v2.0.0
- `monster.schema.json` — v2.0.0
- `poison.schema.json` — v2.0.0
- `rule.schema.json` — v2.0.0
- `skill.schema.json` — v1.0.0
- `spell.schema.json` — v2.0.0
- `table.schema.json` — v2.0.0
- `weapon_property.schema.json` — v1.0.0

---

## License

This work includes material taken from the System Reference Document 5.1
("SRD 5.1") by Wizards of the Coast LLC, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

See `meta.json` for full attribution.
