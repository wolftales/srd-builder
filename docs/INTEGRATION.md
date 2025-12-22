# Downstream Integration Strategy

## Producer-Consumer Relationship

### **The Vision: Separation of Concerns**

srd-builder was created to **remove data processing burden from downstream consumers**, allowing game frameworks and applications to focus purely on game logic and usage. The project was bootstrapped collaboratively with downstream consumers to define the specification and ensure alignment with their consumption needs.

**srd-builder** (Producer/Upstream)
- **Role:** Data extraction and processing specialist
- Extracts structured data directly from SRD 5.1 PDF
- Produces clean, validated JSON data files
- Maintains schemas and metadata
- Version controlled, tested, reproducible
- Implements the spec consumers need

**Consumers** (Downstream)
- **Role:** Game frameworks and application logic
- Defined the data specification and structure requirements
- Integrates srd-builder's data files into game frameworks
- Focuses on game mechanics, not data extraction
- Consumes: data files, schemas, indexes, metadata
- No longer needs to maintain extraction pipeline

## Data Package Structure

srd-builder currently produces the following files for downstream consumption:

```
dist/srd_5_1/
├── data/
│   ├── monsters.json         # 317 creatures with structured fields
│   ├── equipment.json        # 106 equipment items
│   ├── spells.json           # 319 spells with structured effects
│   ├── rules.json            # 172 game rules and mechanics (v0.17.0)
│   ├── tables.json           # 23 reference tables
│   ├── lineages.json         # 13 character lineages
│   ├── classes.json          # 12 character classes
│   └── index.json            # Lookup tables (by_name, by_cr, by_type, etc.)
├── build_report.json         # Build metadata and version info
└── schemas/                  # JSON schemas for validation
    ├── monster.schema.json
    ├── equipment.schema.json
    ├── spell.schema.json
    ├── rule.schema.json      # v0.17.0
    └── ...
```

## What We Provide vs What They Need

### ✅ Currently Available (v0.4.1)
- **data/monsters.json**: 296 monsters with structured AC/HP/Speed
- **data/index.json**: Rich indexes (name, CR, type, size)
- **build_report.json**: Build metadata and versioning
- **schemas/monster.schema.json**: Validation schema

### 🔄 Data Quality Features
1. **Complete extraction**: 296 monsters (100% coverage of SRD 5.1)
2. **Structured AC**: `{"value": 17, "source": "natural armor"}` vs simple `17`
3. **Structured HP**: `{"average": 135, "formula": "18d10+36"}` vs separate fields
4. **Speed conditions**: Preserves `(hover)` and other modifiers
5. **Direct PDF extraction**: Reproducible, version-controlled pipeline

### 📋 Future Content Types
Following the SRD structure, srd-builder will expand to extract:
- ✅ Equipment (weapons, armor, gear) - v0.5.0
- ✅ Classes & Lineages - v0.13.0
- ✅ Spells & Features - v0.6.0
- ✅ Tables - v0.8.3
- ✅ Rules & Mechanics - v0.17.0
- 🔄 Conditions - Future

Each content type follows the same pattern:
```
dist/srd_5_1/
└── data/
    ├── monsters.json     # ✅ v0.5.0 (317 creatures)
    ├── equipment.json    # ✅ v0.5.0 (106 items)
    ├── spells.json       # ✅ v0.6.0 (319 spells)
    ├── rules.json        # ✅ v0.17.0 (172 rules)
    ├── tables.json       # ✅ v0.8.3 (23 tables)
    ├── lineages.json     # ✅ v0.13.0 (13 lineages)
    ├── classes.json      # ✅ v0.13.0 (12 classes)
    ├── conditions.json   # 🔄 Future
    └── index.json        # Unified indexes
```

## Integration Workflow

### For Consumers (Downstream)
1. Pull latest srd-builder release
2. Copy `dist/srd_5_1/data/*` → consumer data directory
3. Use `schemas/` for validation if needed
4. Reference `meta.json` and `build_report.json` for versioning/metadata

---

## Real-World Integration Validation

### Blackmoor Integration Review (v0.8.3 - November 2025)

**Overview:**
The Blackmoor VTT project performed comprehensive real-world integration testing of the v0.8.3 data package across all 6 datasets. This was the first external consumer integration test, providing critical validation of data quality and usability.

**Dataset Quality Assessment:**

| Dataset | Rating | Status | Issues Found |
|---------|--------|--------|--------------|
| Monsters (296) | ⭐⭐⭐⭐⭐ | Production Ready | None - stable since v0.2.0 |
| Equipment (106) | ⭐⭐⭐⭐⭐ | Production Ready | None - v0.8.3 cleanup successful |
| Tables (23) | ⭐⭐⭐⭐⭐ | Production Ready | None - excellent structure |
| Spells (319) | ⭐⭐⭐⭐ | Reference Only | Missing range field (critical) |
| Lineages (13) | ⭐⭐⭐ | Reference Only | Missing ability score increases |
| Classes (12) | ⭐⭐⭐ | Reference Only | Missing primary ability & saves |

**Key Findings:**

✅ **Production Ready (50% of datasets)**
- 3 of 6 datasets are production-ready on first integration
- Structure and extraction quality validated by real usage
- No architectural changes needed

🔴 **Critical Gaps Discovered (Not in TODO.md)**
1. **Lineage ability scores** - Human missing +1 all stats (blocks character creation)
2. **Class primary ability & saves** - Fighter missing Str/Dex and save proficiencies (blocks character sheets)
3. **Spell range field** - All 319 spells missing range (blocks spell targeting/attacks)

**Impact:**
- Identified character creation blockers not visible in internal testing
- Prioritized v0.8.4 work based on real consumer needs
- Validated that extraction approach and structure are sound
- Proved dataset quality when complete (3/3 complete datasets = 5 stars)

**Blackmoor Priorities for v0.8.4:**
1. Add missing fields to lineages (ability scores, subrace links)
2. Add missing fields to classes (primary ability, saving throws)
3. Add range field to all spells
4. Complete spell healing coverage (2% → 100%)

**Lessons Learned:**
- External integration reveals gaps internal testing misses
- Structure quality is excellent when data is complete
- Incomplete extraction (missing fields) != poor design
- Real consumer feedback is invaluable for prioritization

---

### For srd-builder (Producer)
1. Extract content from SRD PDF
2. Normalize and structure data
3. Validate against schema
4. Generate indexes and metadata
5. Tag release
6. Consumers pull the release

## File Format Compatibility

### Naming Convention
Both projects use three-level naming:
- `id`: "monster:aboleth" (stable identifier)
- `simple_name`: "aboleth" (machine-readable)
- `name`: "Aboleth" (display name)

### Field Structure
srd-builder provides RICHER data that consumers can either:
- **Use directly**: Consume structured AC/HP/Speed as-is
- **Flatten**: Convert `{"value": 17, "source": "..."}` → `17` if needed

No data loss - consumers can always extract the simple value from our structured format.

## Current vs Target State

### Current (v0.5.0)
```
srd-builder → [monsters.json, equipment.json, index.json, meta.json, schemas] → Consumers
  296 monsters with full provenance tracking
  111 equipment items with structured parsing
  Structured fields with rich metadata
```

### Target (v1.0)
```
srd-builder → [full SRD data + schemas + provenance] → Consumers
  - Monsters (317) ✅
  - Equipment (106) ✅
  - Spells (319) ✅
  - Rules (172) ✅
  - Tables (23) ✅
  - Lineages (13) ✅
  - Classes (12) ✅
  - Conditions (TBD)
```

## Consumption Examples

### Loading Rules Data

```python
import json

# Load rules dataset
with open("dist/srd_5_1/rules.json") as f:
    rules_data = json.load(f)

# Access metadata
meta = rules_data["_meta"]
print(f"Rules from {meta['source']} (schema v{meta['schema_version']})")

# Access rules
rules = rules_data["items"]
print(f"Loaded {len(rules)} rules")

# Find rules by category
combat_rules = [r for r in rules if r["category"] == "Using Ability Scores"
                and r.get("subcategory") == "Making an Attack"]

# Display a rule
attack_roll = next(r for r in rules if r["id"] == "rule:attack_rolls")
print(f"\n{attack_roll['name']}")
for paragraph in attack_roll["text"]:
    print(f"  {paragraph}")

# Search by tags
action_rules = [r for r in rules if "action" in r.get("tags", [])]
print(f"\nFound {len(action_rules)} rules tagged with 'action'")

# Use index for fast lookup
with open("dist/srd_5_1/index.json") as f:
    index = json.load(f)

# Lookup by name
ability_check_id = index["rules"]["by_name"]["ability_checks"]
# Get from main dataset using ID
ability_check_rule = next(r for r in rules if r["id"] == ability_check_id)

# Browse by category
combat_rule_ids = index["rules"]["by_category"]["Using Ability Scores"]
combat_rules = [r for r in rules if r["id"] in combat_rule_ids]
```

### Cross-Referencing Rules with Other Datasets

```python
# Rules can reference other datasets via cross-reference fields
rule = next(r for r in rules if r["id"] == "rule:concentration")

# Load related spells
if "related_spells" in rule:
    with open("dist/srd_5_1/spells.json") as f:
        spells_data = json.load(f)

    related_spells = [s for s in spells_data["items"]
                     if s["id"] in rule["related_spells"]]
    print(f"Spells requiring concentration: {len(related_spells)}")

# Load related conditions
if "related_conditions" in rule:
    # Future: load conditions.json when available
    pass
```

## Design Philosophy

### **Collaborative Spec, Focused Execution**

- **Consumers define the spec**: Field names, structure, what data is needed
- **srd-builder implements extraction**: PDF parsing, normalization, validation
- **Result**: Clean separation allows each project to excel at its specialty

### **Data Enrichment Strategy**

We provide **richer** data than strictly required:
- Structured fields (AC with sources, HP with formulas) can be flattened if needed
- Additional indexes and metadata available but optional
- Backwards compatible: consumers can ignore enrichments and use simple values

This approach:
- ✅ **No lock-in**: Consumers can use as much or as little structure as needed
- ✅ **Future-proof**: New use cases can leverage richer data without re-extraction
- ✅ **No data loss**: Flattening is always possible, but original detail preserved

## Design Principles

1. **Provide structured fields** that consumers can flatten if needed (no data loss)
   - **Status**: Implemented in v0.4.0 - structured fields with backwards compatibility

2. **Rich indexes** cover common lookups (name, CR, type, size)
   - Additional indexes (alignment, environment, etc.) can be added as needed

3. **Complete provenance** in meta.json (license, PDF hash, page ranges, extraction status)
   - Enables traceability and compliance
   - **Status**: Implemented in v0.5.0

4. **File naming conventions**: Plural for collections (`monsters.json`, `spells.json`)
   - **Status**: Confirmed and consistent across all content types
