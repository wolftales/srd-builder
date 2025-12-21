"""Test class progression table extraction accuracy.

Compares PDF-extracted class progressions against known-good validation data
to ensure extraction quality and catch regressions.

The validation data matches the actual PDF extraction format (ordinals, strings,
em-dash characters) and serves as regression detection for the extraction pipeline.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from validation_data import VALIDATION_CLASS_PROGRESSIONS


@pytest.fixture(scope="module")
def extracted_tables() -> list[dict[str, Any]]:
    """Fixture: Load extracted tables from build output.

    Uses module scope so the JSON file is only loaded once for all tests
    in this module, rather than once per test.
    """
    tables_path = Path("rulesets/srd_5_1/raw/tables_raw.json")
    if not tables_path.exists():
        pytest.skip(f"Tables not found at {tables_path} - run build first")

    with open(tables_path) as f:
        data = json.load(f)
        # Handle both dict with 'tables' key and direct list
        if isinstance(data, dict) and "tables" in data:
            return data["tables"]
        return data if isinstance(data, list) else []


@pytest.fixture(scope="module")
def extracted_progressions(extracted_tables) -> dict[str, dict[str, Any]]:
    """Fixture: Extract just the class progression tables by name.

    Creates a dict mapping class_name -> table_data for easy lookup.
    Depends on extracted_tables fixture.
    """
    progressions = {}
    for table in extracted_tables:
        simple_name = table.get("simple_name", "")
        if simple_name.endswith("_progression"):
            class_name = simple_name.replace("_progression", "")
            progressions[class_name] = table
    return progressions


@pytest.mark.parametrize(
    "class_name",
    [
        "barbarian",
        "bard",
        "cleric",
        "druid",
        "fighter",
        "monk",
        "paladin",
        "ranger",
        "rogue",
        "sorcerer",
        "warlock",
        "wizard",
    ],
)
def test_class_progression_extraction(
    class_name: str, extracted_progressions: dict[str, dict[str, Any]]
):
    """Test that PDF extraction matches validation data for each class."""
    # Get extracted table from fixture
    extracted = extracted_progressions.get(class_name)
    assert extracted is not None, f"Table {class_name}_progression not found in extracted data"

    # Get validation data
    validation = VALIDATION_CLASS_PROGRESSIONS[class_name]

    # Compare row counts
    assert len(extracted["rows"]) == len(
        validation["rows"]
    ), f"{class_name}: Expected {len(validation['rows'])} rows, got {len(extracted['rows'])}"

    # Compare headers (allow some flexibility in format)
    extracted_headers = [str(h).strip() for h in extracted["headers"]]
    validation_headers = [
        str(h).strip() if isinstance(h, str) else h.get("name", str(h))
        for h in validation["headers"]
    ]

    assert (
        len(extracted_headers) == len(validation_headers)
    ), f"{class_name}: Header count mismatch - expected {len(validation_headers)}, got {len(extracted_headers)}"

    # Compare row data (compare string representations for flexibility)
    mismatches = []
    for i, (extracted_row, validation_row) in enumerate(
        zip(extracted["rows"], validation["rows"], strict=False), 1
    ):
        if len(extracted_row) != len(validation_row):
            mismatches.append(
                f"  Row {i}: Column count mismatch - expected {len(validation_row)}, got {len(extracted_row)}"
            )
            continue

        for j, (extracted_val, validation_val) in enumerate(
            zip(extracted_row, validation_row, strict=False)
        ):
            # Normalize for comparison (handle 0 vs "—" for spell slots)
            extracted_str = str(extracted_val).strip()
            validation_str = str(validation_val).strip()

            # Allow "0" to match "—" (common in spell slot columns)
            if extracted_str in ("0", "—") and validation_str in ("0", "—"):
                continue

            if extracted_str != validation_str:
                header = extracted_headers[j] if j < len(extracted_headers) else f"Column {j}"
                mismatches.append(
                    f"  Row {i}, {header}: expected '{validation_str}', got '{extracted_str}'"
                )

    if mismatches:
        pytest.fail(
            f"{class_name} progression has {len(mismatches)} mismatches:\n"
            + "\n".join(mismatches[:10])
        )


def test_all_classes_present(extracted_progressions: dict[str, dict[str, Any]]):
    """Test that all 12 class progressions are extracted."""
    extracted_classes = set(extracted_progressions.keys())

    expected_classes = set(VALIDATION_CLASS_PROGRESSIONS.keys())

    missing = expected_classes - extracted_classes
    assert not missing, f"Missing class progressions: {missing}"

    extra = extracted_classes - expected_classes
    assert not extra, f"Unexpected class progressions: {extra}"


if __name__ == "__main__":
    # Allow running directly for quick validation
    pytest.main([__file__, "-v"])
