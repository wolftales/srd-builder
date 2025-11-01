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

### 🔄 Data Quality Features
1. **Complete extraction**: 296 monsters (100% coverage of SRD 5.1)
2. **Structured AC**: `{"value": 17, "source": "natural armor"}` vs simple `17`
3. **Structured HP**: `{"average": 135, "formula": "18d10+36"}` vs separate fields
4. **Speed conditions**: Preserves `(hover)` and other modifiers
5. **Direct PDF extraction**: Reproducible, version-controlled pipeline

### 📋 Future Content Types
Following the SRD structure, srd-builder will expand to extract:
- Week 2: Equipment (weapons, armor, gear)
- Week 3-4: Classes & Lineages
- Week 5: Spells & Features
- Week 6: Conditions, Rules, Tables

Each content type will follow the same pattern:
```
dist/srd_5_1/
└── data/
    ├── monsters.json     # ✅ v0.5.0 (296 monsters)
    ├── equipment.json    # ✅ v0.5.0 (111 items)
    ├── classes.json      # 🔄 Future
    ├── spells.json       # 🔄 Future
    ├── conditions.json   # 🔄 Future
    └── index.json        # Unified indexes
```

## Integration Workflow

### For Consumers (Downstream)
1. Pull latest srd-builder release
2. Copy `dist/srd_5_1/data/*` → consumer data directory
3. Use `schemas/` for validation if needed
4. Reference `meta.json` and `build_report.json` for versioning/metadata

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
  - Monsters (296) ✅
  - Equipment (111) ✅
  - Classes (TBD)
  - Spells (TBD)
  - Conditions/Rules/Tables (TBD)
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
