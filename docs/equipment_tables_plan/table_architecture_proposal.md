# Table Architecture: Three-Layer System

**Date:** 2025-11-01
**Purpose:** Clarify three different "table" concepts and how they interact
**Status:** Proposed architecture for discussion

---

## The Three Layers

### Layer 1: Discovery (Builder Internal)
**File:** `raw/table_discovery.json`
**Purpose:** Extraction tool - documents PDF table structures
**Audience:** Extraction scripts, builders
**Lifecycle:** Generated during initial PDF scan, rarely updated

### Layer 2: Index (Public API)
**File:** `dist/srd_5_1/index_tables.json`
**Purpose:** Search/reference - makes tables findable
**Audience:** Search systems, UIs, consumers
**Lifecycle:** Generated after extraction, updated when datasets change

### Layer 3: Content (Public Data)
**File:** `dist/srd_5_1/data/tables.json` or embedded in datasets
**Purpose:** Game mechanics - actual table data for gameplay
**Audience:** Game engines, consumers
**Lifecycle:** Extracted from SRD, versioned with content

---

## Layer 1: Discovery (Internal)

### Location
```
rulesets/srd_5_1/raw/table_discovery.json
```

### Purpose
Document all tables found in source PDF for extraction tooling.

### Schema (from GPT's proposal)
```json
{
  "_meta": {
    "discovered_at": "2025-11-01T12:00:00Z",
    "total_tables": 47,
    "source": "SRD_CC_v5.1.pdf",
    "pages_scanned": "1-403"
  },
  "tables": [
    {
      "id": "table:armor-light",
      "title": "Light Armor",
      "page_start": 63,
      "page_end": 63,
      "row_count": 2,
      "headers": ["Armor", "Cost", "Armor Class (AC)", "Strength", "Stealth", "Weight"],
      "context": "equipment",
      "section": "Armor and Shields",
      "table_type": "data"
    },
    {
      "id": "table:barbarian-level",
      "title": "The Barbarian",
      "page_start": 14,
      "page_end": 14,
      "row_count": 20,
      "headers": ["Level", "Proficiency Bonus", "Features", "Rages", "Rage Damage"],
      "context": "classes",
      "section": "Classes",
      "table_type": "progression"
    },
    {
      "id": "table:treasure-hoard-cr-0-4",
      "title": "Treasure Hoard: Challenge 0-4",
      "page_start": 136,
      "page_end": 136,
      "row_count": 12,
      "headers": ["d100", "Coins", "Magic Items"],
      "context": "treasure",
      "section": "Treasure",
      "table_type": "reference"
    }
  ]
}
```

### Usage
```python
# Used by extraction scripts
def extract_armor_items(pdf_path):
    discovery = load_json('raw/table_discovery.json')
    armor_tables = [t for t in discovery['tables']
                    if 'armor' in t['id']]

    for table_meta in armor_tables:
        column_map = build_column_map(table_meta['headers'])
        items = extract_table(pdf_path, table_meta, column_map)
```

### Key Points
- ❌ NOT published to dist/ (internal only)
- ❌ NOT for end users
- ✅ Generated once during initial scan
- ✅ Used by all extraction scripts
- ✅ Includes ALL tables (even non-game tables like pricing references)

---

## Layer 2: Index (Public Reference)

### Location
```
dist/srd_5_1/index_tables.json
```

### Purpose
Searchable index of game-relevant tables, integrated with main index.

### Schema (Proposed)
```json
{
  "_meta": {
    "id": "index_tables",
    "version": "1.0.0",
    "generated_at": "2025-11-01T14:30:00Z",
    "parent_index": "index.json",
    "table_count": 35
  },
  "tables": [
    {
      "id": "table:armor",
      "title": "Armor",
      "type": "equipment_data",
      "description": "Armor types with AC, cost, and properties",
      "categories": ["light", "medium", "heavy"],
      "page": 63,
      "source": "SRD 5.1",
      "data_file": "equipment.json",
      "data_filter": {"category": "armor"}
    },
    {
      "id": "table:barbarian-progression",
      "title": "Barbarian Level Progression",
      "type": "class_progression",
      "description": "Level-by-level features, rages, and rage damage",
      "page": 14,
      "source": "SRD 5.1",
      "data_file": "classes.json",
      "data_path": "classes.barbarian.level_progression"
    },
    {
      "id": "table:treasure-hoard-cr-0-4",
      "title": "Treasure Hoard: Challenge 0-4",
      "type": "reference_table",
      "description": "Random treasure generation for CR 0-4 encounters",
      "page": 136,
      "source": "SRD 5.1",
      "data_file": "tables.json",
      "data_path": "treasure.hoards.cr_0_4"
    }
  ]
}
```

### Integration with Main Index
```json
// dist/srd_5_1/index.json
{
  "_meta": {
    "id": "srd_5_1",
    "version": "1.0.0"
  },
  "indices": {
    "items": "index_items.json",
    "spells": "index_spells.json",
    "classes": "index_classes.json",
    "tables": "index_tables.json"  // <-- New!
  },
  "datasets": {
    "equipment": "data/equipment.json",
    "spells": "data/spells.json",
    "tables": "data/tables.json"
  }
}
```

### Usage
```javascript
// Consumer: "Show me all tables about treasure"
const tableIndex = await fetch('/dist/srd_5_1/index_tables.json');
const treasureTables = tableIndex.tables.filter(t =>
  t.type === 'reference_table' && t.title.includes('Treasure')
);

// Consumer: "What table has armor AC values?"
const armorTable = tableIndex.tables.find(t =>
  t.id === 'table:armor'
);
// Load actual data
const equipment = await fetch(armorTable.data_file);
const armorItems = equipment.filter(armorTable.data_filter);
```

### Key Points
- ✅ Published to dist/ (public)
- ✅ For consumers/search/UI
- ✅ Only game-relevant tables (no pricing references)
- ✅ Points to where data lives
- ✅ Searchable by type, title, description

---

## Layer 3: Content (Actual Data)

### Two Patterns

#### Pattern A: Embedded in Datasets
**For:** Data tables (armor, weapons, spells)
**Example:** Armor table data lives in `equipment.json`

```json
// equipment.json already contains the "armor table" data
{
  "equipment": [
    {"id": "item:leather", "armor_class": {"base": 11}, ...},
    {"id": "item:chain-shirt", "armor_class": {"base": 13}, ...}
  ]
}
```

**Index points to it:**
```json
{
  "id": "table:armor",
  "data_file": "equipment.json",
  "data_filter": {"category": "armor"}
}
```

#### Pattern B: Dedicated tables.json
**For:** Reference tables (treasure, encounters, random tables)
**Example:** Treasure tables in `tables.json`

```json
// dist/srd_5_1/data/tables.json
{
  "_meta": {
    "id": "tables",
    "version": "1.0.0",
    "description": "Reference tables for treasure, encounters, and random generation"
  },
  "treasure": {
    "hoards": {
      "cr_0_4": {
        "id": "treasure:hoard-cr-0-4",
        "name": "Treasure Hoard: Challenge 0-4",
        "roll": "1d100",
        "page": 136,
        "entries": [
          {
            "roll_range": "01-06",
            "coins": {"cp": 0, "sp": "6d6*100", "ep": 0, "gp": "3d6*10", "pp": 0},
            "magic_items": 0
          },
          {
            "roll_range": "07-16",
            "coins": {"cp": 0, "sp": "6d6*100", "ep": 0, "gp": "3d6*10", "pp": 0},
            "magic_items": {
              "count": "2d6",
              "table": "magic-item-a"
            }
          }
        ]
      }
    }
  },
  "encounters": {
    // Future: Random encounter tables
  }
}
```

**Index points to it:**
```json
{
  "id": "table:treasure-hoard-cr-0-4",
  "data_file": "tables.json",
  "data_path": "treasure.hoards.cr_0_4"
}
```

---

## How They Work Together

### Example Flow: Extracting Equipment

```
1. DISCOVERY (one-time setup)
   └─> Run discover_tables.py
       └─> Generates raw/table_discovery.json
           └─> Documents all PDF tables

2. EXTRACTION (uses discovery)
   └─> Run extract_equipment.py
       └─> Reads raw/table_discovery.json
       └─> Finds armor/weapon/gear tables
       └─> Extracts items
       └─> Writes dist/data/equipment.json

3. INDEXING (after extraction)
   └─> Run build_indices.py
       └─> Reads equipment.json
       └─> Creates index_tables.json entry:
           {
             "id": "table:armor",
             "data_file": "equipment.json",
             "data_filter": {"category": "armor"}
           }
       └─> Writes dist/index_tables.json
```

### Example Flow: Extracting Treasure Tables

```
1. DISCOVERY (already done)
   └─> raw/table_discovery.json already has treasure table metadata

2. EXTRACTION (new!)
   └─> Run extract_tables.py
       └─> Reads raw/table_discovery.json
       └─> Finds treasure tables
       └─> Parses roll ranges, results
       └─> Writes dist/data/tables.json

3. INDEXING (after extraction)
   └─> Run build_indices.py
       └─> Reads tables.json
       └─> Creates index_tables.json entry:
           {
             "id": "table:treasure-hoard-cr-0-4",
             "data_file": "tables.json",
             "data_path": "treasure.hoards.cr_0_4"
           }
```

---

## Relationships Diagram

```
┌─────────────────────────────────────────────────────┐
│ LAYER 1: Discovery (Internal)                      │
│ raw/table_discovery.json                            │
│ • All tables in PDF                                 │
│ • Headers, pages, row counts                        │
│ • Used by extraction scripts                        │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Used by extractors
                  ▼
┌─────────────────────────────────────────────────────┐
│ EXTRACTION SCRIPTS                                  │
│ • extract_equipment.py                              │
│ • extract_classes.py                                │
│ • extract_tables.py (future)                        │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Generates
                  ▼
┌─────────────────────────────────────────────────────┐
│ LAYER 3: Content (Public Data)                     │
│ dist/data/equipment.json ◄──┐                       │
│ dist/data/classes.json       │                      │
│ dist/data/tables.json        │ Points to            │
└─────────────────┬────────────┼──────────────────────┘
                  │            │
                  │ Indexed by │
                  ▼            │
┌─────────────────────────────┼─────────────────────┐
│ LAYER 2: Index (Public Search)                   │
│ dist/index_tables.json       │                    │
│ • Searchable table metadata  │                    │
│ • Points to data files  ─────┘                    │
└───────────────────────────────────────────────────┘
```

---

## Decision Matrix

### Question 1: Do we need both Discovery + Index?

**YES** - They serve different purposes:

| Aspect | Discovery | Index |
|--------|-----------|-------|
| Audience | Builders | Consumers |
| Location | raw/ | dist/ |
| Scope | ALL tables | Game tables only |
| Purpose | Extraction | Search/reference |
| Updates | Rare | After each extraction |

### Question 2: How does index_tables.json relate to index.json?

**Option A: Child File (Recommended)**
```json
// index.json
{
  "indices": {
    "tables": "index_tables.json"
  }
}
```

**Option B: Embedded**
```json
// index.json
{
  "tables": [
    {"id": "table:armor", ...},
    {"id": "table:treasure", ...}
  ]
}
```

**Recommendation:** Option A - keeps index.json focused, allows table index to grow

### Question 3: Where does table content live?

**Two patterns (both valid):**

**Pattern A: Embedded in datasets**
- Armor table → equipment.json
- Class progression → classes.json
- **Pro:** Data already extracted
- **Con:** Requires filtering to get "table view"

**Pattern B: Dedicated tables.json**
- Treasure tables → tables.json
- Encounter tables → tables.json
- **Pro:** Clean separation
- **Con:** Additional extraction work

**Recommendation:** Use both patterns based on table type:
- **Data tables** (armor, spells) → Embedded in dataset
- **Reference tables** (treasure, encounters) → tables.json

---

## Implementation Phases

### Phase 0.5: Table Discovery (Week 2)
```markdown
- [ ] Create discover_tables.py script
- [ ] Generate raw/table_discovery.json
- [ ] Update extractors to use discovery
- [ ] Document discovery process
```

**Output:** `raw/table_discovery.json`

### Phase 1.5: Table Index (Week 3)
```markdown
- [ ] Create build_indices.py enhancement
- [ ] Generate index_tables.json
- [ ] Link to index.json
- [ ] Document index structure
```

**Output:** `dist/index_tables.json`

### Phase 5: Reference Tables (Future)
```markdown
- [ ] Create extract_tables.py
- [ ] Extract treasure tables
- [ ] Extract encounter tables
- [ ] Generate tables.json
```

**Output:** `dist/data/tables.json`

---

## Schema Summary

### Discovery Schema (Layer 1)
**File:** `schemas/table_discovery.schema.json`
**Status:** Proposed by GPT, approved with enhancements
**Purpose:** Validate table discovery output

### Index Schema (Layer 2)
**File:** `schemas/index_tables.schema.json`
**Status:** NEW - needs creation
**Purpose:** Validate table index structure

### Content Schema (Layer 3)
**File:** `schemas/tables.schema.json`
**Status:** Future - defer until treasure table extraction
**Purpose:** Validate reference table content

---

## Questions for You

1. **Discovery timing:** Week 2 (after equipment fixes) or Week 1 (before)?

2. **Index scope:** Start with equipment tables only, or index all known tables?

3. **Index structure:** Child file (index_tables.json) or embedded in index.json?

4. **Content pattern:** Okay to use both embedded (armor) and dedicated (treasure)?

5. **Schema priority:** Create all three schemas now, or just discovery for Week 2?

---

## My Recommendations

### Immediate (Week 2)
1. ✅ Implement table discovery (Layer 1)
2. ✅ Create discovery schema
3. ✅ Use discovery in equipment extraction

### Soon (Week 3)
1. ✅ Create table index (Layer 2)
2. ✅ Create index schema
3. ✅ Link to main index.json
4. ✅ Index equipment tables initially

### Later (Weeks 5+)
1. ✅ Extract treasure tables (Layer 3)
2. ✅ Create tables.json
3. ✅ Create content schema
4. ✅ Expand index to include all tables

---

## Example: Complete Flow

### User wants to find armor AC values

**Step 1: Search the index**
```javascript
const index = await fetch('/dist/srd_5_1/index_tables.json');
const armorTable = index.tables.find(t => t.id === 'table:armor');
// Returns: {data_file: "equipment.json", data_filter: {category: "armor"}}
```

**Step 2: Load the data**
```javascript
const equipment = await fetch(`/dist/srd_5_1/data/${armorTable.data_file}`);
const armorItems = equipment.equipment.filter(item =>
  item.category === armorTable.data_filter.category
);
// Returns: [{id: "item:leather", armor_class: {base: 11}}, ...]
```

### User wants treasure for CR 0-4 encounter

**Step 1: Search the index**
```javascript
const index = await fetch('/dist/srd_5_1/index_tables.json');
const treasureTable = index.tables.find(t =>
  t.id === 'table:treasure-hoard-cr-0-4'
);
// Returns: {data_file: "tables.json", data_path: "treasure.hoards.cr_0_4"}
```

**Step 2: Load the table**
```javascript
const tables = await fetch(`/dist/srd_5_1/data/${treasureTable.data_file}`);
const treasure = get_nested(tables, treasureTable.data_path);
// Returns: {roll: "1d100", entries: [{roll_range: "01-06", ...}]}
```

---

## Summary

**Three layers, three purposes:**

1. **Discovery** (raw/) - For builders, documents PDF structure
2. **Index** (dist/) - For search, makes tables findable
3. **Content** (dist/data/) - For consumers, actual table data

**All three are valuable:**
- Discovery helps extraction (Week 2)
- Index helps search (Week 3)
- Content provides data (ongoing)

**They're related but distinct:**
- Discovery → used by extractors
- Index → used by search/UI
- Content → used by game logic

**Next decision:** When to build each layer?
