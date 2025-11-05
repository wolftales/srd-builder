# Quick Reference: Table Migration

**For migrating table extraction to new SRD versions (e.g., 5.1 → 5.2.1)**

See [TABLE_MIGRATION_GUIDE.md](TABLE_MIGRATION_GUIDE.md) for complete documentation.

## Quick Start

### 1. Discover Coordinates

```bash
# Find Y-coordinates for a table
python scripts/discover_table_coordinates.py \
    rulesets/srd_5_2_1/SRD_CC_v5.2.1.pdf \
    armor \
    63 64
```

### 2. Update Parser

```python
# In text_table_parser.py, update Y-ranges:
rows = extract_multipage_rows(
    pdf_path,
    [
        {"page": pages[0], "y_min": 680, "y_max": 750},  # ← Update these
        {"page": pages[1], "y_min": 70, "y_max": 430},
    ],
)
```

### 3. Validate

```bash
# Build and check counts
make output
python scripts/validate_table_counts.py rulesets/srd_5_2_1/raw/tables_raw.json
```

## Parser Tiers

| Tier | Complexity | Lines | Examples | Key Utilities |
|------|-----------|-------|----------|--------------|
| 1 | Simple single-region | 30-40 | `exchange_rates`, `donning_doffing_armor` | `extract_region_rows()` |
| 2 | Categories/special logic | 50-60 | `tools`, `food_drink_lodging` | `detect_indentation()`, `find_currency_index()` |
| 3 | Multi-page complex | 70-90 | `armor`, `weapons`, `adventure_gear` | `extract_multipage_rows()`, `group_words_by_y()` |

## Common Y-Coordinate Issues

**Problem:** Missing rows (e.g., "Expected 13, found 11")
**Solution:** Expand Y-range by ±10-20 points

```python
# Too restrictive
{"page": 66, "y_min": 70, "y_max": 440}  # Misses items at Y=456-501

# Fixed
{"page": 66, "y_min": 70, "y_max": 510}  # Includes all items
```

**Best Practice:** Always add ±10 buffer to discovered ranges

## Migration Checklist

- [ ] Diff PDFs to identify changes
- [ ] Run `discover_table_coordinates.py` for each table
- [ ] Update page numbers in `reference_data.py`
- [ ] Update Y-coordinate ranges in parsers
- [ ] Update expected counts in `validate_table_counts.py`
- [ ] Build: `make output`
- [ ] Validate: `python scripts/validate_table_counts.py ...`
- [ ] Test: `pytest tests/test_table_parsers.py`

## Key Files

| File | Purpose |
|------|---------|
| `src/srd_builder/table_extraction/text_table_parser.py` | Table parsers |
| `src/srd_builder/table_extraction/text_parser_utils.py` | Reusable utilities |
| `src/srd_builder/table_extraction/reference_data.py` | Table metadata (pages, parsers) |
| `scripts/discover_table_coordinates.py` | Find Y-coordinates |
| `scripts/validate_table_counts.py` | Validate row counts |

## Example: Migrating Armor Table

```bash
# 1. Discover coordinates
python scripts/discover_table_coordinates.py rulesets/srd_5_2_1/SRD.pdf armor 63 64

# Output shows:
#   Page 63: Data Y range: 689.7 to 689.7
#   Page 64: Data Y range: 71.9 to 226.7
#   Suggested range (rounded): y_min=680, y_max=690 (p63), y_min=70, y_max=230 (p64)

# 2. Update parser in text_table_parser.py
# Change:
#   {"page": pages[0], "y_min": 680, "y_max": 750},
#   {"page": pages[1], "y_min": 70, "y_max": 430},
# To:
#   {"page": pages[0], "y_min": 680, "y_max": 690},
#   {"page": pages[1], "y_min": 70, "y_max": 230},

# 3. Validate
make output
python scripts/validate_table_counts.py rulesets/srd_5_2_1/raw/tables_raw.json
# Should show: ✓ armor 13 rows (expected 13)
```

## Utility Functions Quick Reference

```python
# Extract from single page region
extract_region_rows(pdf_path, page, y_min=100, y_max=400)

# Extract from multiple pages
extract_multipage_rows(pdf_path, [
    {"page": 63, "y_min": 680, "y_max": 750},
    {"page": 64, "y_min": 70, "y_max": 430},
])

# Group words by Y-coordinate (for manual processing)
group_words_by_y(words, tolerance=2)

# Convert to sorted text rows
rows_to_sorted_text(rows)

# Find currency position
find_currency_index(words_list)  # Returns index of gp/sp/cp

# Detect indentation (for categories)
detect_indentation(words, indent_threshold=60)

# Filter headers
should_skip_header(words_list, header_keywords=["Name", "Cost"])
```

## Tips

1. **Start with Tier 1 tables** - Simplest to migrate
2. **Validate continuously** - Build after each tier
3. **Add ±10 buffer** - Y-coordinates need breathing room
4. **Document surprises** - Note structural changes for next migration
5. **Compare outputs** - Diff old vs new SRD to verify correctness

---

**See [TABLE_MIGRATION_GUIDE.md](TABLE_MIGRATION_GUIDE.md) for complete documentation.**
