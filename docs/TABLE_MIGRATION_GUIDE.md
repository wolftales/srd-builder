# Table Migration Guide

Guide for migrating table extraction to new SRD versions (e.g., 5.1 → 5.2.1).

## Overview

The table extraction system uses coordinate-based PDF parsing with reusable utilities. Most migrations only require updating page numbers and Y-coordinate ranges, not rewriting parsers.

## Table Parser Complexity Tiers

### Tier 1 - Simple Single-Region (30-40 lines)
**Characteristics:**
- Single page, single Y-coordinate range
- Straightforward row structure (no categories or columns)
- Examples: `exchange_rates`, `donning_doffing_armor`

**Utilities Used:**
- `extract_region_rows()` - Extract from specific page region
- `rows_to_sorted_text()` - Convert coordinates to sorted text

**Template:**
```python
def parse_simple_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    from .text_parser_utils import extract_region_rows, rows_to_sorted_text

    rows = extract_region_rows(pdf_path, pages[0], y_min=100, y_max=400)

    for _y_pos, words_list in rows_to_sorted_text(rows):
        # Filter and parse rows
        pass
```

### Tier 2 - Categories or Special Logic (50-60 lines)
**Characteristics:**
- Single page but with subcategories
- Indentation detection needed
- Special transformations (e.g., saddle types)
- Examples: `tools`, `food_drink_lodging`, `tack_harness_vehicles`

**Utilities Used:**
- `extract_region_rows()` or `group_words_by_y()`
- `detect_indentation()` - Check if row is indented
- `find_currency_index()` - Locate cost markers

**Template:**
```python
def parse_category_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    from .text_parser_utils import extract_region_rows, detect_indentation, find_currency_index

    # Track categories
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None

    for row in rows:
        is_indented = detect_indentation(row_words, indent_threshold=60)

        if is_category_header:
            current_category = header_name
            categories[current_category] = {"row_index": i, "items": []}
        elif current_category and is_indented:
            categories[current_category]["items"].append(...)

    return {"headers": headers, "rows": items, "categories": categories}
```

### Tier 3 - Multi-Page Complex (70-90 lines)
**Characteristics:**
- Spans multiple pages
- Complex multi-column layouts
- Category sections + varied data
- Examples: `armor`, `weapons`, `adventure_gear`

**Utilities Used:**
- `extract_multipage_rows()` - Merge rows from multiple pages
- `group_words_by_y()` - For two-column layouts
- `detect_indentation()` - For nested categories

**Template:**
```python
def parse_complex_table(pdf_path: str, pages: list[int]) -> dict[str, Any]:
    from .text_parser_utils import extract_multipage_rows, rows_to_sorted_text

    rows = extract_multipage_rows(
        pdf_path,
        [
            {"page": pages[0], "y_min": 680, "y_max": 750},
            {"page": pages[1], "y_min": 70, "y_max": 430},
        ],
    )

    for _y_pos, words in rows_to_sorted_text(rows):
        # Parse with special logic
        pass
```

## Migration Workflow

### Phase 1: Discovery & Documentation

1. **Diff PDFs to identify changes**
```bash
# Extract text from both PDFs
pdftotext rulesets/srd_5_1/SRD_CC_v5.1.pdf old.txt
pdftotext rulesets/srd_5_2_1/SRD_CC_v5.2.1.pdf new.txt

# Compare page counts and structure
diff -u old.txt new.txt | grep "^+\|^-" | head -50
```

2. **Run table discovery script**
```bash
python scripts/discover_tables.py rulesets/srd_5_2_1/SRD_CC_v5.2.1.pdf
```

3. **Classify each table by tier**
   - Review output from discovery script
   - Note: simple (Tier 1), categories (Tier 2), or multi-page (Tier 3)
   - Document in `TABLE_METADATA` (see below)

### Phase 2: Coordinate Discovery

4. **Find exact Y-coordinate ranges**
```bash
# Use the coordinate discovery script
python scripts/discover_table_coordinates.py \
    rulesets/srd_5_2_1/SRD_CC_v5.2.1.pdf \
    armor \
    63 64
```

5. **Document ranges with ±10 buffer**
   - Always add 10-point buffer to discovered ranges
   - Round to nearest 10 for readability
   - Example: Discovered Y=71.9-434.6 → Use Y=70-440

### Phase 3: Metadata Update

6. **Update `reference_data.py`**
```python
TEXT_PARSED_TABLES = {
    "armor": {
        "parser": "parse_armor_table",
        "pages": [63, 64],  # ← Update if changed
    },
    # ... other tables
}
```

7. **Create/update table metadata documentation**
```python
# In reference_data.py or new tables_metadata.py
TABLE_METADATA = {
    "armor": {
        "pages": [63, 64],
        "tier": 3,  # Tier 1/2/3
        "structure": "multipage",  # "single_page", "two_column", "multipage"
        "spans": [
            {"page": 63, "y_range": (680, 750), "content": "Padded only"},
            {"page": 64, "y_range": (70, 430), "content": "12 armor items"},
        ],
        "expected_rows": 13,
        "categories": None,  # or ["Light", "Medium", "Heavy"]
        "markers": ["gp", "lb."],  # Key text to identify data rows
        "notes": "Padded appears alone on p63, rest on p64",
    },
}
```

### Phase 4: Parser Updates

8. **Update coordinate ranges in parsers**

For each parser in `text_table_parser.py`:

**Tier 1 (Single-region):**
```python
# OLD
rows = extract_region_rows(pdf_path, pages[0], y_min=530, y_max=590)

# NEW (update page and/or coordinates)
rows = extract_region_rows(pdf_path, pages[0], y_min=540, y_max=600)
```

**Tier 3 (Multi-page):**
```python
# OLD
rows = extract_multipage_rows(
    pdf_path,
    [
        {"page": pages[0], "y_min": 680, "y_max": 750},
        {"page": pages[1], "y_min": 70, "y_max": 430},
    ],
)

# NEW (update coordinates based on discovery)
rows = extract_multipage_rows(
    pdf_path,
    [
        {"page": pages[0], "y_min": 690, "y_max": 750},
        {"page": pages[1], "y_min": 70, "y_max": 440},
    ],
)
```

9. **Update expected row counts**
```python
# Update validation
if len(parsed_rows) != 13:  # ← Update if count changed
    logging.warning(...)
```

### Phase 5: Validation

10. **Run build and check output**
```bash
python -m srd_builder.build --ruleset srd_5_2_1 --out dist

# Check for warnings
# Expected output: "✓ Extracted N tables"
```

11. **Validate table counts**
```bash
# Check each table extracted correct number of rows
python scripts/validate_table_counts.py rulesets/srd_5_2_1/raw/tables_raw.json
```

12. **Compare outputs semantically**
```bash
# Diff old vs new to verify data correctness (not exact match due to SRD changes)
python scripts/compare_srd_versions.py \
    rulesets/srd_5_1/tables.json \
    rulesets/srd_5_2_1/tables.json
```

### Phase 6: Testing

13. **Run unit tests**
```bash
pytest tests/test_table_parsers.py -v
```

14. **Spot-check 3 parsers** (one from each tier)
   - Tier 1: Check `exchange_rates`
   - Tier 2: Check `tools` (has categories)
   - Tier 3: Check `armor` (multi-page)

15. **Verify special cases still work**
   - Category metadata preserved
   - Saddle subcategory transformations
   - Two-column layouts (adventure_gear)
   - Indentation detection

## Common Issues & Solutions

### Issue: Missing rows (e.g., "Expected 13, found 11")

**Cause:** Y-coordinate range too restrictive

**Solution:**
1. Run coordinate discovery script for that table
2. Check actual Y-coordinates of missing items
3. Expand Y-range by ±10-20 points
4. Rebuild and validate

Example:
```python
# Too restrictive - misses items at Y=456-501
{"page": 66, "y_min": 70, "y_max": 440}

# Fixed - includes all items
{"page": 66, "y_min": 70, "y_max": 510}
```

### Issue: Extra rows extracted (garbage data)

**Cause:** Y-coordinate range too permissive, catching headers/footers

**Solution:**
1. Tighten Y-range to exclude non-data rows
2. Improve row filtering logic (check for required markers)
3. Add header skip logic using `should_skip_header()`

### Issue: Category metadata lost

**Cause:** Category detection logic not preserved during refactor

**Solution:**
1. Verify `is_category_header` detection still works
2. Check indentation threshold is correct for new PDF
3. Ensure `categories` dict is returned in result

### Issue: Two-column layout broken

**Cause:** Column split X-coordinate changed in new PDF

**Solution:**
1. Print X-coordinates of left/right column words
2. Adjust `column_split` threshold (usually around 300)
3. Test with items from both columns

## Coordinate Discovery Best Practices

### Always Add Buffer to Y-Ranges

```python
# Discovered: Y=71.9 to Y=434.6
# Use: Y=70 to Y=440 (round to tens, add buffer)
```

**Why:** PDF word extraction can vary slightly. Buffer prevents edge cases.

### Use Markers to Validate Ranges

```python
# When discovering armor coordinates, look for cost markers
armor_words = [w for w in words if 'gp' in w[4] and 'lb.' in nearby_words]
y_range = (min(w[1] for w in armor_words), max(w[1] for w in armor_words))
```

### Document What's in Each Range

```python
# BAD - no context
{"page": 63, "y_min": 680, "y_max": 750}

# GOOD - explains what this range contains
{"page": 63, "y_min": 680, "y_max": 750}  # Bottom of p63 (Padded at Y=689)
```

## Testing Strategy

### Unit Tests for Counts

```python
# tests/test_table_parsers.py
@pytest.mark.parametrize("table_name,expected_count", [
    ("armor", 13),
    ("weapons", 37),
    ("tools", 20),
])
def test_table_extraction_counts(table_name, expected_count, srd_pdf_path):
    """Verify each table extracts expected number of rows."""
    parser_func = get_parser_for_table(table_name)
    pages = get_pages_for_table(table_name)

    result = parser_func(srd_pdf_path, pages)
    assert len(result["rows"]) == expected_count, \
        f"Expected {expected_count} rows, got {len(result['rows'])}"
```

### Integration Test

```python
def test_all_tables_extract(srd_pdf_path):
    """Verify all tables extract without errors."""
    from srd_builder.table_extraction.extractor import extract_all_tables

    result = extract_all_tables(srd_pdf_path)

    # Should extract all tables
    assert len(result["tables"]) >= 37

    # No tables should have extraction errors
    for table in result["tables"]:
        assert "error" not in table
```

## Utility Function Reference

### Core Extraction Functions

**`extract_region_rows(pdf_path, page, y_min=None, y_max=None, x_min=None, x_max=None)`**
- Extract rows from specific page region
- Use for: Single-page tables (Tier 1)
- Returns: `dict[float, list[tuple[float, str]]]` (Y-coord → words)

**`extract_multipage_rows(pdf_path, page_specs)`**
- Extract and merge rows from multiple pages
- Use for: Multi-page tables (Tier 3)
- Page spec: `{"page": int, "y_min": float, "y_max": float, ...}`
- Returns: `dict[float, list[tuple[float, str]]]`

**`group_words_by_y(words, tolerance=2)`**
- Group PDF words by Y-coordinate (rows)
- Use for: Manual word processing, two-column layouts
- Returns: `dict[float, list[tuple[float, str]]]`

### Row Processing Functions

**`rows_to_sorted_text(rows)`**
- Convert coordinate dict to sorted text rows
- Use for: Final row iteration in parsers
- Returns: `Iterator[tuple[float, list[str]]]`

**`find_currency_index(words_list)`**
- Find position of currency marker (gp/sp/cp)
- Use for: Parsing cost columns
- Returns: `int` (index) or `-1`

**`split_at_currency(words_list, currency_idx)`**
- Split row at currency position
- Use for: Separating name from cost
- Returns: `tuple[list[str], list[str]]`

### Filtering Functions

**`should_skip_header(words_list, header_keywords=None)`**
- Check if row is a header (not data)
- Use for: Filtering out table headers
- Returns: `bool`

**`detect_indentation(words, indent_threshold=60)`**
- Check if row is indented (category item)
- Use for: Category detection, nested items
- Returns: `bool`

## Migration Checklist

Use this checklist for each new SRD version:

- [ ] Phase 1: Discovery
  - [ ] Diff PDFs to identify structural changes
  - [ ] Run `discover_tables.py` on new PDF
  - [ ] Classify each table by tier (1/2/3)

- [ ] Phase 2: Coordinates
  - [ ] Run `discover_table_coordinates.py` for each table
  - [ ] Document Y-ranges with ±10 buffer
  - [ ] Note any page number changes

- [ ] Phase 3: Metadata
  - [ ] Update page numbers in `reference_data.py`
  - [ ] Update/create `TABLE_METADATA` entries
  - [ ] Document expected row counts

- [ ] Phase 4: Parser Updates
  - [ ] Update Y-coordinate ranges in all parsers
  - [ ] Update expected row counts in validations
  - [ ] Test special cases (categories, columns)

- [ ] Phase 5: Validation
  - [ ] Run full build: `make output`
  - [ ] Check for extraction warnings
  - [ ] Validate row counts match expectations
  - [ ] Compare old vs new SRD outputs

- [ ] Phase 6: Testing
  - [ ] Run unit tests: `pytest tests/test_table_parsers.py`
  - [ ] Spot-check one parser from each tier
  - [ ] Verify category metadata preserved
  - [ ] Verify special logic still works

- [ ] Phase 7: Documentation
  - [ ] Update CHANGELOG with migration notes
  - [ ] Document any parser logic changes
  - [ ] Note any SRD structural differences

## Tips for Success

1. **Migrate incrementally**: Start with Tier 1 (simple) tables, then Tier 2, then Tier 3
2. **Validate continuously**: Run build after updating each tier
3. **Use git branches**: Create `srd-5.2.1-migration` branch for work
4. **Compare diffs carefully**: New SRD may have legitimate data changes (not bugs)
5. **Document surprises**: Note any unexpected PDF structure changes for future migrations
6. **Preserve special logic**: Don't over-simplify parsers that have complex requirements
7. **Test edge cases**: Category headers, multi-line items, special characters
8. **Keep utilities generic**: Resist adding SRD-version-specific code to utils

## Future Improvements

Consider adding these utilities for easier migrations:

1. **`detect_column_split(words)`** - Auto-detect two-column layouts
2. **`normalize_currency(text)`** - Standardize currency formats
3. **`merge_continued_items(rows)`** - Handle items spanning multiple lines
4. **`validate_table_structure(result, metadata)`** - Auto-validate against metadata
5. **Coordinate discovery as a library function** - Call from tests, not just scripts

## Questions?

See also:
- `docs/ROADMAP.md` - Overall project structure and plans
- `src/srd_builder/table_extraction/text_parser_utils.py` - Utility function implementations
- `src/srd_builder/table_extraction/text_table_parser.py` - Parser examples
- `scripts/discover_tables.py` - Table discovery tool
