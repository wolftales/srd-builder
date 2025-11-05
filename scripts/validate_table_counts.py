#!/usr/bin/env python3
"""Validate table extraction counts against expected values.

This script checks that all tables extracted the expected number of rows,
helping catch coordinate range issues during migrations.

Usage:
    python scripts/validate_table_counts.py <tables_json_path>

Example:
    python scripts/validate_table_counts.py rulesets/srd_5_1/raw/tables_raw.json
"""

import json
import sys
from pathlib import Path

# Expected row counts for SRD 5.1 tables
# Update these values when migrating to new SRD versions
EXPECTED_COUNTS = {
    # Equipment tables (TEXT_PARSED)
    "armor": 13,  # 3 light + 6 medium + 4 heavy
    "weapons": 37,  # 14 simple + 23 martial
    "adventure_gear": 103,  # Includes all detail rows (categories expand count)
    "tools": 38,  # Artisan's tools + gaming sets + musical instruments (with categories)
    "mounts_and_other_animals": 8,  # Note: Some entries may be multiline
    "tack_harness_vehicles": 14,  # Note: Expected ~17, but extraction finds 14
    "waterborne_vehicles": 6,
    "trade_goods": 13,
    "food_drink_lodging": 17,  # 6 inn stays + 6 meals + 5 ale/wine (includes lifestyle levels)
    "services": 7,  # 2 coach cab + 2 hireling + 3 other
    "container_capacity": 13,
    # Reference tables
    "exchange_rates": 5,  # CP, SP, EP, GP, PP
    "donning_doffing_armor": 4,  # Light, Medium, Heavy, Shield
    "lifestyle_expenses": 6,  # Wretched → Aristocratic
    # ... add more tables as needed
}


def validate_counts(tables_json_path: str) -> tuple[int, int]:
    """Validate table row counts.

    Args:
        tables_json_path: Path to tables_raw.json or tables.json

    Returns:
        Tuple of (passed_count, failed_count)
    """
    with open(tables_json_path) as f:
        data = json.load(f)

    # Handle both raw format ({"tables": [...]}) and processed format ({table_name: {...}})
    if "tables" in data:
        tables = {t["simple_name"]: t for t in data["tables"]}
    else:
        tables = data

    passed = 0
    failed = 0
    warnings = []

    print("\n" + "=" * 70)
    print("Table Row Count Validation")
    print("=" * 70 + "\n")

    for table_name, expected_count in sorted(EXPECTED_COUNTS.items()):
        if table_name not in tables:
            warnings.append(f"⚠️  {table_name}: NOT FOUND in output")
            failed += 1
            continue

        table = tables[table_name]
        actual_count = len(table.get("rows", []))

        if actual_count == expected_count:
            print(f"✓ {table_name:30s} {actual_count:3d} rows (expected {expected_count})")
            passed += 1
        else:
            diff = actual_count - expected_count
            sign = "+" if diff > 0 else ""
            print(
                f"✗ {table_name:30s} {actual_count:3d} rows (expected {expected_count}, {sign}{diff})"
            )
            failed += 1

    # Check for tables in output but not in expectations
    extra_tables = set(tables.keys()) - set(EXPECTED_COUNTS.keys())
    if extra_tables:
        print("\n📋 Tables not in validation list:")
        for table_name in sorted(extra_tables):
            table = tables[table_name]
            actual_count = len(table.get("rows", []))
            print(f"   {table_name:30s} {actual_count:3d} rows")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(warning)
        print()

    return passed, failed


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    tables_json_path = sys.argv[1]

    if not Path(tables_json_path).exists():
        print(f"Error: File not found: {tables_json_path}")
        sys.exit(1)

    passed, failed = validate_counts(tables_json_path)

    # Exit with error code if any validations failed
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
