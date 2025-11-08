"""Test to enforce elimination of legacy parser code.

This test ensures that all tables have been migrated to modern pattern-based extraction.
Skip with: pytest -k "not legacy" while working on migration.
"""

from srd_builder.table_extraction.table_metadata import TABLES


def test_no_legacy_parser_tables():
    """Fail if ANY table still uses legacy_parser pattern.

    This is a hard fence to prevent legacy code from lingering.
    All tables should use modern pattern-based extraction.
    """
    legacy_tables = [
        name for name, config in TABLES.items() if config.get("pattern_type") == "legacy_parser"
    ]

    assert (
        len(legacy_tables) == 0
    ), f"Found {len(legacy_tables)} tables still using legacy_parser: {sorted(legacy_tables)}"


def test_legacy_parser_migration_progress():
    """Track migration progress - this test always runs.

    Shows how many tables remain to migrate.
    """
    legacy_tables = [
        name for name, config in TABLES.items() if config.get("pattern_type") == "legacy_parser"
    ]

    total_tables = len(TABLES)
    modern_tables = total_tables - len(legacy_tables)
    progress_pct = (modern_tables / total_tables * 100) if total_tables > 0 else 0

    print(f"\n{'='*60}")
    print(f"TABLE MIGRATION PROGRESS: {modern_tables}/{total_tables} ({progress_pct:.1f}%)")
    print(f"{'='*60}")

    if len(legacy_tables) > 0:
        print(f"\nRemaining legacy_parser tables ({len(legacy_tables)}):")
        for name in sorted(legacy_tables):
            pages = TABLES[name].get("pages", [])
            rows = TABLES[name].get("validation", {}).get("expected_rows", "?")
            print(f"  - {name:30} pages {pages} ({rows} rows)")

        print(f"\n⚠️  WARNING: {len(legacy_tables)} tables still using legacy_parser pattern")
        print("Run migration, then remove @skip from test_no_legacy_parser_tables()")
    else:
        print("\n✅ All tables migrated to modern patterns!")
        print("Remember to:")
        print("  1. Delete text_table_parser.py")
        print("  2. Remove legacy_parser from patterns.py")
        print("  3. Remove @skip from test_no_legacy_parser_tables()")

    # This test always passes - just shows progress
    assert True
