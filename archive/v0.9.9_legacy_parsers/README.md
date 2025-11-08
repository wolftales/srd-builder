# Legacy Parser Archive (v0.9.9)

This directory contains legacy table parsing code that has been **replaced** by modern pattern-based extraction.

## Migration Complete: 30/30 Tables (100%)

As of v0.9.9, **all tables** now use modern pattern-based extraction via `table_metadata.py`:
- 28 tables using `split_column` pattern
- 2 tables using `simple_region` pattern
- 0 tables using `legacy_parser` pattern

## Archived Files

### `text_table_parser.py` (1313 lines)
Legacy table-specific parsing functions. Each table had its own custom parser:
- `parse_armor_table()`
- `parse_weapons_table()`
- `parse_adventure_gear_table()`
- `parse_tools_table()`
- ... and 12 more

**Replaced by:** Generic pattern-based extraction in `patterns.py` + `table_metadata.py` configuration.

### `_extract_legacy_parser()` (from patterns.py)
Bridge function that called legacy parsers during migration. No longer needed.

### `extractor.py` legacy imports
Large import block and parser mapping dict for legacy functions. Can be removed.

## Why Archive Instead of Delete?

1. **Reference:** Legacy parsers contain domain knowledge about table layouts and edge cases
2. **Safety:** If modern extraction has issues, we can reference the old approach
3. **Documentation:** Shows the evolution from custom parsers to generic patterns
4. **Testing:** Can verify modern extraction produces same results as legacy

## Related Cleanup (Not Yet Done)

These files may still have dependencies on monsters/spells parsing:
- `text_parser_utils.py` - Shared utilities (may still be used)
- `patterns.py` - Contains `_extract_legacy_parser()` function (can be removed)
- `extractor.py` - Contains legacy parser imports/mapping (can be removed)

## Safe to Delete?

**YES** - `text_table_parser.py` can be safely deleted:
- ✅ All 30 tables migrated to modern patterns
- ✅ No tables use `legacy_parser` pattern
- ✅ All tests passing with modern extraction
- ✅ Data quality equal or better than legacy

**MAYBE** - Other files need investigation:
- `text_parser_utils.py` - Check if used by monsters/spells parsing
- Legacy code in `patterns.py` and `extractor.py` - Can be removed but low priority

## Archived: 2025-11-08

Archived after successful migration of all 30 tables to modern pattern-based extraction.
