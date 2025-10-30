# Blackmoor Integration Strategy

## Producer-Consumer Relationship

**srd-builder** (Producer/Upstream)
- Extracts structured data directly from SRD 5.1 PDF
- Produces clean, validated JSON data files
- Maintains schemas and metadata
- Version controlled, tested, reproducible

**Blackmoor** (Consumer/Downstream)
- Integrates srd-builder's data files into game framework
- Replaces their manually-curated/incomplete data
- Consumes: data files, schemas, indexes, metadata

## Data Package Structure

srd-builder currently produces the following files for Blackmoor consumption:

```
dist/srd_5_1/
├── data/
│   ├── monsters.json         # 296 monsters with structured fields
│   └── index.json            # Lookup tables (by_name, by_cr, by_type, etc.)
├── build_report.json         # Build metadata and version info
└── [schemas TBD]             # JSON schemas for validation
```

## What We Provide vs What They Need

### ✅ Currently Available (v0.4.1)
- **data/monsters.json**: 296 monsters with structured AC/HP/Speed
- **data/index.json**: Rich indexes (name, CR, type, size)
- **build_report.json**: Build metadata and versioning
- **schemas/monster.schema.json**: Validation schema

### 🔄 Data Improvements Over Blackmoor
1. **+95 more monsters** (296 vs 201)
2. **Structured AC**: `{"value": 17, "source": "natural armor"}` vs simple `17`
3. **Structured HP**: `{"average": 135, "formula": "18d10+36"}` vs separate fields
4. **Speed conditions**: Preserves `(hover)` and other modifiers
5. **Direct PDF extraction**: Reproducible, version-controlled pipeline

### 📋 Future Content Types (Weeks 2-6)
Following Blackmoor's roadmap, srd-builder will expand to extract:
- Week 2: Equipment (weapons, armor, gear)
- Week 3-4: Classes & Lineages
- Week 5: Spells & Features
- Week 6: Conditions, Rules, Tables

Each content type will follow the same pattern:
```
dist/srd_5_1/
└── data/
    ├── monsters.json     # ✅ v0.4.1
    ├── equipment.json    # 🔄 Week 2
    ├── classes.json      # 🔄 Week 3-4
    ├── spells.json       # 🔄 Week 5
    ├── conditions.json   # 🔄 Week 6
    └── index.json        # Updated with all content types
```

## Integration Workflow

### For Blackmoor (Consumer)
1. Pull latest srd-builder release
2. Copy `dist/srd_5_1/data/*` → Blackmoor data directory
3. Use `schemas/` for validation if needed
4. Reference `build_report.json` for versioning/metadata

### For srd-builder (Producer)
1. Extract content from SRD PDF
2. Normalize and structure data
3. Validate against schema
4. Generate indexes
5. Tag release
6. Blackmoor pulls the release

## File Format Compatibility

### Naming Convention
Both projects use three-level naming:
- `id`: "monster:aboleth" (stable identifier)
- `simple_name`: "aboleth" (machine-readable)
- `name`: "Aboleth" (display name)

### Field Structure
srd-builder provides RICHER data that Blackmoor can either:
- **Use directly**: Consume structured AC/HP/Speed as-is
- **Flatten**: Convert `{"value": 17, "source": "..."}` → `17` if needed

No data loss - Blackmoor can always extract the simple value from our structured format.

## Current vs Target State

### Current (v0.4.1)
```
srd-builder → [monsters.json, index.json, schemas] → Blackmoor
  296 monsters                                          201 monsters
  Structured fields                                     Simple fields
```

### Target (v1.0)
```
srd-builder → [full SRD data + schemas] → Blackmoor
  - Monsters (296) ✅
  - Equipment (TBD)
  - Classes (TBD)
  - Spells (TBD)
  - Conditions/Rules/Tables (TBD)
```

## Open Questions
1. Should we maintain Blackmoor's exact field structure, or provide structured fields they can flatten?
   - **Recommendation**: Provide structured, they flatten if needed (no data loss)

2. Do they need additional index types beyond name/CR/type/size?
   - Current indexes cover common lookups

3. Should build_report.json include extraction statistics (warnings, coverage)?
   - Currently minimal, can expand if useful

4. File naming: `monsters.json` vs `monster.json`?
   - Currently plural, matches collection semantics
