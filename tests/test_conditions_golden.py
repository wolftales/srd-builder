"""Golden tests for condition extraction validation.

Validates that all 15 conditions extract cleanly without cross-contamination
from the actual SRD PDF. This is an integration test that catches regressions
in the full extraction pipeline.
"""

from pathlib import Path

import pytest

from srd_builder.extract.extract_conditions import extract_conditions


@pytest.fixture
def pdf_path():
    """Path to SRD PDF for testing."""
    path = Path("SRD_CC_v5.1.pdf")
    if not path.exists():
        pytest.skip(f"PDF not found: {path}")
    return path


def test_all_conditions_extract_cleanly(pdf_path):
    """Validate all 15 conditions extract without cross-contamination.

    This is a regression test for the case-sensitivity and column-ordering
    bugs that were fixed in the prose extraction framework.

    Bugs caught by this test:
    - Grappled section truncated at "incapacitated" reference
    - Prone section receiving Blinded text due to column misalignment
    """
    result = extract_conditions(pdf_path)

    # All 15 conditions present
    assert (
        len(result["conditions"]) == 15
    ), f"Expected 15 conditions, got {len(result['conditions'])}"

    # No warnings about cross-contamination
    assert result["_meta"]["total_warnings"] == 0, (
        f"Expected 0 warnings, got {result['_meta']['total_warnings']}: "
        f"{result['_meta'].get('warnings', [])}"
    )


def test_grappled_section_boundary_integrity(pdf_path):
    """Test that Grappled section contains full text without truncation.

    Regression test for case-insensitive matching bug where "incapacitated"
    in Grappled's text was matched as the Incapacitated header.
    """
    result = extract_conditions(pdf_path)

    grappled = next((c for c in result["conditions"] if c["name"] == "Grappled"), None)
    assert grappled is not None, "Grappled condition not found"

    # Should contain the full text including the end
    assert (
        "reach of the grappler" in grappled["raw_text"]
    ), "Grappled section appears truncated - missing ending text"

    # Should NOT contain the next section's header (Incapacitated)
    # Note: It SHOULD contain lowercase "incapacitated" (valid reference)
    assert (
        "Incapacitated" not in grappled["raw_text"]
    ), "Grappled section contains Incapacitated header - boundary contamination"

    # Verify the cross-reference is preserved (lowercase is OK)
    assert (
        "incapacitated" in grappled["raw_text"].lower()
    ), "Grappled section missing valid 'incapacitated' cross-reference"


def test_all_condition_names_present(pdf_path):
    """Verify all expected condition names are extracted."""
    result = extract_conditions(pdf_path)

    expected_conditions = {
        "Blinded",
        "Charmed",
        "Deafened",
        "Exhaustion",
        "Frightened",
        "Grappled",
        "Incapacitated",
        "Invisible",
        "Paralyzed",
        "Petrified",
        "Poisoned",
        "Prone",
        "Restrained",
        "Stunned",
        "Unconscious",
    }

    extracted_names = {c["name"] for c in result["conditions"]}

    assert extracted_names == expected_conditions, (
        f"Condition name mismatch:\n"
        f"  Missing: {expected_conditions - extracted_names}\n"
        f"  Extra: {extracted_names - expected_conditions}"
    )


def test_condition_text_length_sanity(pdf_path):
    """Verify all conditions have reasonable text lengths.

    Too short: likely truncated
    Too long: likely merged with another condition
    """
    result = extract_conditions(pdf_path)

    min_length = 50  # Even brief conditions have ~50 chars
    max_length = 2000  # Most conditions are 200-500 chars; Exhaustion ~800

    outliers = []
    for cond in result["conditions"]:
        text_len = len(cond["raw_text"])
        if text_len < min_length or text_len > max_length:
            outliers.append((cond["name"], text_len))

    assert len(outliers) == 0, (
        f"Found {len(outliers)} conditions with abnormal text lengths:\n"
        + "\n".join(f"  {name}: {length} chars" for name, length in outliers)
    )


def test_no_capitalized_cross_contamination(pdf_path):
    """Verify no condition section contains another's capitalized header.

    Lowercase references (e.g., "is prone") are OK.
    Capitalized headers (e.g., "Prone A prone creature...") indicate bleeding.
    """
    result = extract_conditions(pdf_path)

    all_names = {c["name"] for c in result["conditions"]}
    contamination_found = []

    for cond in result["conditions"]:
        name = cond["name"]
        text = cond["raw_text"]

        # Check if this section contains OTHER condition headers
        # (its own name at the start is expected)
        for other_name in all_names:
            if other_name == name:
                continue

            # Look for capitalized occurrence (header, not reference)
            # After the first occurrence of this condition's own name
            first_name_pos = text.find(name)
            if first_name_pos == -1:
                continue

            remaining_text = text[first_name_pos + len(name) :]
            if other_name in remaining_text:
                contamination_found.append(f"{name} contains '{other_name}' header")

    assert len(contamination_found) == 0, (
        f"Found {len(contamination_found)} cases of cross-contamination:\n"
        + "\n".join(f"  - {case}" for case in contamination_found)
    )
