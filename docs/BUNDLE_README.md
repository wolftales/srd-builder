# SRD 5.1 Dataset Bundle

**Version:** srd-builder v0.4.2
**Schema Version:** 1.1.0
**Generated:** October 31, 2025
**Source:** System Reference Document 5.1 (SRD_CC_v5.1)

---

## What's Included

Machine-readable D&D 5e SRD data extracted from official PDF:

- **296 Monsters** - Full stat blocks (schema v1.1.0)
- **114 Equipment Items** - Weapons, armor, gear (schema v1.1.0)
- **Search Index** - Pre-built lookups

---

## Quick Start

```javascript
const data = require('./data/monsters.json');
const dragon = data.items.find(m => m.simple_name === 'adult_red_dragon');
console.log(dragon.challenge_rating);  // 17
```

```python
import json
with open('data/monsters.json') as f:
    monsters = json.load(f)['items']
dragon = next(m for m in monsters if m['id'] == 'monster:adult_red_dragon')
```

---

## Bundle Contents

```
srd_5_1/
├── README.md
├── build_report.json      # Build process metadata
├── data/
│   ├── meta.json          # Dataset catalog & license
│   ├── monsters.json      # 296 creature stat blocks
│   ├── equipment.json     # 114 items
│   └── index.json         # Search index
├── schemas/
│   ├── monster.schema.json
│   └── equipment.schema.json
└── docs/
    ├── SCHEMAS.md         # Schema design & versioning
    └── DATA_DICTIONARY.md # Field reference & SRD mappings
```

---

## Documentation

**Read these files for detailed information:**

- **SCHEMAS.md** - Schema v1.1.0 design, versioning, use cases, evolution history
- **DATA_DICTIONARY.md** - Complete field reference with SRD source mappings
- **meta.json** - License, attribution, file manifest
- **build_report.json** - Extraction statistics
- **schemas/*.json** - JSON Schema validation

---

## Key Features

- **Namespaced IDs:** `monster:aboleth`, `item:longsword`
- **Structured data:** AC, HP, speeds as objects (not strings)
- **Normalized names:** `simple_name` for search/indexing
- **Schema validation:** All data validates against JSON Schema Draft 2020-12

```bash
jsonschema -i data/monsters.json schemas/monster.schema.json
```

---

## License & Attribution

**License:** [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/)

**Required Attribution:**
> This work includes material taken from the System Reference Document 5.1 ("SRD 5.1") by Wizards of the Coast LLC. The SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License.

**Conversion:** [srd-builder](https://github.com/wolftales/srd-builder) v0.4.2

Full license in `meta.json`.
