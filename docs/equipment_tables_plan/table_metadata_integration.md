# Table Metadata Schema: Strategic Integration

**Date:** 2025-11-01
**Status:** Proposed by GPT - Under Evaluation
**Decision:** Recommended as Phase 0.5 (after bug fixes, before spells)

---

## What This Is

**NOT:** Game content tables (treasure, encounters)
**IS:** Metadata about PDF table structures discovered during extraction

**Purpose:** Document table locations, headers, and structure to improve extraction reliability

---

## Example Table Metadata

```json
{
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
      "source": "SRD_CC_v5.1.pdf"
    },
    {
      "id": "table:armor-medium",
      "title": "Medium Armor",
      "page_start": 63,
      "page_end": 63,
      "row_count": 6,
      "headers": ["Armor", "Cost", "Armor Class (AC)", "Strength", "Stealth", "Weight"],
      "context": "equipment",
      "section": "Armor and Shields",
      "source": "SRD_CC_v5.1.pdf"
    },
    {
      "id": "table:weapons-simple-melee",
      "title": "Simple Melee Weapons",
      "page_start": 66,
      "page_end": 66,
      "row_count": 8,
      "headers": ["Name", "Cost", "Damage", "Weight", "Properties"],
      "context": "equipment",
      "section": "Weapons",
      "source": "SRD_CC_v5.1.pdf"
    }
  ],
  "_meta": {
    "discovered_at": "2025-11-01T12:00:00Z",
    "total_tables": 15,
    "pages_scanned": "62-73"
  }
}
```

---

## How This Helps Your Current Problem

### Problem: Column Detection Fails
**Current approach:** Assume column[2] = AC
**Fails because:** Column positions vary across tables

**With table metadata:**
```python
# Discovery phase (run once)
def discover_tables(pdf):
    """Find all tables, capture their headers"""
    tables = []
    for page in pdf:
        for table in page.find_tables():
            tables.append({
                'id': generate_table_id(table),
                'headers': table.header,  # Actual column names!
                'page': page.number,
                # ...
            })
    return tables

# Extraction phase (uses discovered metadata)
def extract_armor_items(pdf, table_metadata):
    """Use metadata to map columns correctly"""
    armor_tables = [t for t in table_metadata if 'armor' in t['id']]

    for table_meta in armor_tables:
        # Build column map from KNOWN headers
        column_map = build_column_map(table_meta['headers'])
        # column_map = {'ac': 2, 'cost': 1, 'weight': 5, ...}

        # Extract rows with correct mapping
        rows = extract_table_rows(pdf, table_meta)
        for row in rows:
            ac = row[column_map['ac']]  # Always correct!
            cost = row[column_map['cost']]
```

**Key insight:** Headers captured during discovery, used during extraction

---

## Integration with Strategic Plan

### Where It Fits

**Current Plan:**
```
Phase 1: Fix equipment bugs
Phase 2: Extract patterns
Phase 3: Spells extraction
```

**Enhanced Plan:**
```
Phase 1: Fix equipment bugs (immediate workarounds)
Phase 0.5: Discover table metadata (OPTIONAL)
Phase 2: Extract patterns (use metadata if available)
Phase 3: Spells extraction
```

### Two Approaches

#### Approach A: Add Discovery Step (Recommended)
```python
# New extraction pipeline
def build_equipment():
    # Step 0: Discover tables (new!)
    table_metadata = discover_tables(pdf)
    write_json(table_metadata, 'raw/table_metadata.json')

    # Step 1: Extract using metadata
    raw_items = extract_equipment(pdf, table_metadata)

    # Step 2: Parse
    parsed_items = parse_equipment(raw_items)

    # Step 3: Postprocess
    final_items = postprocess(parsed_items)
```

**Benefits:**
- ✅ More reliable column detection
- ✅ Easier debugging (know what tables exist)
- ✅ Validates extraction completeness
- ✅ Helps with future datasets

**Cost:**
- 2-3 hours to implement discovery
- Additional JSON file to maintain

#### Approach B: Inline Discovery (Simpler)
```python
# No separate file, just use during extraction
def extract_equipment(pdf):
    for page in pdf:
        tables = page.find_tables()
        for table in tables:
            # Discover headers inline
            headers = table.header
            column_map = build_column_map(headers)

            # Extract immediately
            rows = extract_rows(table, column_map)
```

**Benefits:**
- ✅ No new files
- ✅ Simpler pipeline

**Cost:**
- ❌ Can't validate what tables exist
- ❌ No debugging metadata
- ❌ Rediscovers tables each run

---

## Recommendation: Phase 0.5 (After Equipment Fixes)

### Timeline

**Week 1 (Now):** Fix equipment bugs WITHOUT table metadata
- Use inline header detection (Approach B)
- Get equipment working correctly
- Don't block on discovery infrastructure

**Week 2:** Add table discovery (Phase 0.5)
- Implement `discover_tables()` function
- Generate `table_metadata.json`
- Refactor extraction to use metadata
- Validate against equipment bugs (should be even more robust)

**Week 3+:** Use for future datasets
- Discover class tables, spell lists
- Use metadata for validation
- Document table coverage

### Rationale

**Why not now:**
- Equipment bugs can be fixed without it (inline header detection works)
- Don't want to block bug fixes on new infrastructure
- Copilot's concern: "fix what's broken first"

**Why next week:**
- Once equipment works, this makes it MORE robust
- Sets pattern for classes (level tables, spell slot tables)
- Good time to add it (between bugs and new datasets)

**Why at all:**
- Makes column detection bulletproof
- Documents PDF structure (useful reference)
- Enables validation ("did we extract all tables?")

---

## Schema Assessment

### GPT's Proposed Schema: APPROVED with Minor Tweaks

```json
{
  "$id": "https://srd-builder.local/schemas/tables.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SRD Table Metadata (v1.0.0)",
  "description": "Metadata about PDF table structures discovered during extraction. Used for column mapping, validation, and documentation.",
  "type": "object",
  "required": ["_meta", "tables"],
  "properties": {
    "tables": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "page_start", "headers", "context", "source"],
        "properties": {
          "id": {
            "type": "string",
            "pattern": "^table:",
            "description": "Unique table identifier (e.g., table:armor-light, table:weapons-simple-melee)"
          },
          "title": {
            "type": "string",
            "description": "Table title as it appears in PDF (e.g., 'Light Armor')"
          },
          "page_start": {
            "type": "integer",
            "description": "First page where table appears"
          },
          "page_end": {
            "type": ["integer", "null"],
            "description": "Last page if table spans multiple pages"
          },
          "row_count": {
            "type": ["integer", "null"],
            "description": "Number of data rows (excluding headers)"
          },
          "headers": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Column header labels exactly as extracted from PDF"
          },
          "context": {
            "type": "string",
            "enum": ["equipment", "classes", "spells", "lineages", "conditions", "monsters", "other"],
            "description": "Dataset grouping this table belongs to"
          },
          "section": {
            "type": ["string", "null"],
            "description": "PDF section header (e.g., 'Armor and Shields', 'Weapons')"
          },
          "subsection": {
            "type": ["string", "null"],
            "description": "PDF subsection header (e.g., 'Light Armor', 'Simple Melee Weapons')"
          },
          "source": {
            "type": "string",
            "description": "Source PDF filename"
          },
          "table_type": {
            "type": ["string", "null"],
            "enum": ["data", "reference", "progression", "pricing", null],
            "description": "OPTIONAL: Classification of table purpose"
          },
          "bbox": {
            "type": ["array", "null"],
            "items": { "type": "number" },
            "minItems": 4,
            "maxItems": 4,
            "description": "OPTIONAL: Bounding box [x0, y0, x1, y1] for debugging"
          },
          "confidence": {
            "type": ["number", "null"],
            "minimum": 0,
            "maximum": 1,
            "description": "OPTIONAL: Confidence score for table detection heuristics"
          },
          "notes": {
            "type": ["string", "null"],
            "description": "OPTIONAL: Extraction notes or issues"
          }
        },
        "additionalProperties": false
      }
    },
    "_meta": {
      "type": "object",
      "required": ["discovered_at", "total_tables", "source"],
      "properties": {
        "discovered_at": {
          "type": "string",
          "format": "date-time",
          "description": "Timestamp when tables were discovered"
        },
        "total_tables": {
          "type": "integer",
          "description": "Total number of tables discovered"
        },
        "source": {
          "type": "string",
          "description": "Source document analyzed"
        },
        "pages_scanned": {
          "type": "string",
          "description": "Page range scanned (e.g., '62-73')"
        },
        "extractor_version": {
          "type": ["string", "null"],
          "description": "Version of extraction code used"
        }
      }
    }
  },
  "additionalProperties": false
}
```

**Changes from GPT's proposal:**
1. ✅ Added `subsection` field (matches context tracking pattern)
2. ✅ Added `table_type` enum (data vs reference vs progression)
3. ✅ Made some fields optional (bbox, confidence, notes)
4. ✅ Wrapped tables in `tables` array with `_meta` sibling (matches equipment.json pattern)
5. ✅ Added `context` enum with known datasets

---

## Usage Patterns

### Pattern 1: Discovery During Initial Extraction
```python
# scripts/discover_tables.py
def discover_all_tables(pdf_path):
    """
    One-time discovery of all tables in PDF.
    Creates table_metadata.json for use by extractors.
    """
    pdf = fitz.open(pdf_path)
    tables = []

    for page_num in range(len(pdf)):
        page = pdf[page_num]

        # Find tables on page
        for table in page.find_tables():
            tables.append({
                'id': generate_table_id(table, page_num),
                'headers': extract_headers(table),
                'page_start': page_num,
                'source': pdf_path,
                # ...
            })

    return {
        'tables': tables,
        '_meta': {
            'discovered_at': datetime.now().isoformat(),
            'total_tables': len(tables),
            'source': pdf_path
        }
    }
```

### Pattern 2: Use Metadata During Extraction
```python
# extract_equipment.py
def extract_equipment(pdf_path, table_metadata_path):
    """Extract equipment using discovered table metadata"""

    # Load table metadata
    table_metadata = load_json(table_metadata_path)

    # Find equipment tables
    equipment_tables = [
        t for t in table_metadata['tables']
        if t['context'] == 'equipment'
    ]

    items = []
    for table_meta in equipment_tables:
        # Build column map from metadata
        column_map = build_column_map(table_meta['headers'])

        # Extract items using correct columns
        table_items = extract_from_table(
            pdf_path,
            table_meta['page_start'],
            table_meta['id'],
            column_map
        )
        items.extend(table_items)

    return items
```

### Pattern 3: Validation
```python
# validate_extraction.py
def validate_equipment_extraction(equipment_json, table_metadata):
    """Verify all tables were extracted"""

    equipment_tables = [
        t for t in table_metadata['tables']
        if t['context'] == 'equipment'
    ]

    for table in equipment_tables:
        # Check: Did we extract all rows?
        expected_rows = table['row_count']
        extracted_rows = count_items_from_table(equipment_json, table['id'])

        if extracted_rows < expected_rows:
            print(f"WARNING: {table['id']} - expected {expected_rows}, got {extracted_rows}")
```

---

## Relationship to "Game Tables" (Future)

**This schema:** PDF table metadata (structure)
**Future schema:** Game content tables (treasure, encounters)

**Example of the difference:**

**Table Metadata (this schema):**
```json
{
  "id": "table:treasure-hoard-cr-0-4",
  "title": "Treasure Hoard: Challenge 0-4",
  "headers": ["d100", "Coins", "Magic Items"],
  "page_start": 136,
  "context": "treasure"
}
```

**Game Table (future schema - different!):**
```json
{
  "id": "treasure:hoard-cr-0-4",
  "name": "Treasure Hoard: Challenge 0-4",
  "roll": "1d100",
  "entries": [
    {"roll": "01-06", "coins": "...", "magic_items": 0},
    {"roll": "07-16", "coins": "...", "magic_items": "Roll on Magic Item Table A"}
  ]
}
```

**Key difference:**
- Table metadata = PDF structure documentation
- Game tables = Extracted game content

Both are useful, but serve different purposes!

---

## Decision Matrix

### Do It Now (Week 1)
**IF:**
- You're blocked on column detection
- Equipment bugs can't be fixed without it
- You want infrastructure before bug fixes

**THEN:** Implement discovery + metadata before fixes

### Do It Next (Week 2) - RECOMMENDED
**IF:**
- Equipment bugs can be fixed with inline detection
- You want working extraction first
- Infrastructure can enhance existing solution

**THEN:** Fix bugs now, add discovery next week

### Defer It (Week 3+)
**IF:**
- Equipment working fine without it
- Worried about scope creep
- Want to validate need with spells first

**THEN:** Wait until classes extraction (definitely needs it for level tables)

---

## My Recommendation

### Phase It Like This:

**Week 1: Equipment Bugs (No metadata)**
```python
# Quick fix: Inline header detection
def extract_armor(table):
    headers = table.header  # Get headers
    column_map = map_columns(headers)  # Map on the fly
    return extract_rows(table, column_map)
```

**Week 2: Add Table Discovery (Enhance)**
```python
# Better: Pre-discover tables
table_metadata = discover_tables(pdf)
equipment = extract_equipment(pdf, table_metadata)
```

**Week 3+: Use for All Datasets**
```python
# Spells: Might not need (no tables?)
# Classes: Definitely needs (level progression tables)
# Monsters: Might need (stat block tables?)
```

---

## Implementation Checklist (When You Do It)

```markdown
- [ ] Create `discover_tables.py` script
- [ ] Implement header extraction
- [ ] Generate `table_metadata.json`
- [ ] Update extraction to use metadata
- [ ] Add validation script
- [ ] Document discovery process
- [ ] Test: Do column mappings improve?
```

---

## Summary

**Status:** Great idea from GPT, not blocking, add after bug fixes

**Recommendation:** Phase 0.5 (Week 2)

**Schema:** Approved with minor enhancements

**Benefits:** More robust extraction, validation, documentation

**Cost:** 2-3 hours implementation, additional JSON file

**Decision:** YES, but don't block equipment fixes on it

---

## Questions for You

1. **Timing:** Fix bugs first then add discovery (Week 2)? Or discovery first (Week 1)?

2. **Scope:** Just equipment tables, or discover ALL tables in one pass (classes, spells, etc.)?

3. **Validation:** Want automated validation (compare extracted rows to table metadata)?

4. **Storage:** One `table_metadata.json` for entire SRD, or per-dataset (`equipment_tables.json`, `class_tables.json`)?

My vote: **Week 2, equipment only, yes to validation, single file**
