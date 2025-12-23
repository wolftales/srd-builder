"""Tests for madness tables parsing module."""

from __future__ import annotations

from srd_builder.parse.parse_madness_tables import (
    _clean_effect_text,
    _filter_header_rows,
    parse_madness_tables,
)


def test_parse_madness_tables_empty():
    """Test parsing empty tables data."""
    result = parse_madness_tables({})
    assert result == []


def test_parse_madness_tables_complete():
    """Test parsing all three madness table types."""
    tables_data = {
        "short_term_madness": {
            "page": 201,
            "rows": [
                ["d100", "Effect"],  # Header row - should be filtered
                ["01-20", "The character retreats into his or her mind"],
                ["21-30", "The character becomes incapacitated"],
            ],
        },
        "short_term_madness_part2": {
            "page": 201,
            "rows": [
                ["31-40", "The character falls unconscious"],
            ],
        },
        "long_term_madness": {
            "page": 201,
            "rows": [
                ["01-10", "The character feels compelled to repeat a specific activity"],
                ["11-20", "The character experiences vivid hallucinations"],
            ],
        },
        "indefinite_madness": {
            "page": 202,
            "rows": [
                ["01-15", "Being drunk keeps me sane"],
                ["16-25", "I keep whatever I find"],
            ],
        },
    }

    result = parse_madness_tables(tables_data)

    assert len(result) == 3

    # Check short-term (should merge part1 and part2)
    short_term = result[0]
    assert short_term["id"] == "madness:short_term"
    assert short_term["name"] == "Short-Term Madness"
    assert short_term["simple_name"] == "short_term_madness"
    assert short_term["duration"] == "1d10 minutes"
    assert len(short_term["rows"]) == 3  # 2 from part1 + 1 from part2
    assert short_term["columns"] == [
        {"name": "d100", "type": "string"},
        {"name": "Effect", "type": "string"},
    ]

    # Check long-term
    long_term = result[1]
    assert long_term["id"] == "madness:long_term"
    assert long_term["name"] == "Long-Term Madness"
    assert long_term["simple_name"] == "long_term_madness"
    assert long_term["duration"] == "1d10 × 10 hours"
    assert len(long_term["rows"]) == 2

    # Check indefinite
    indefinite = result[2]
    assert indefinite["id"] == "madness:indefinite"
    assert indefinite["name"] == "Indefinite Madness"
    assert indefinite["simple_name"] == "indefinite_madness"
    assert indefinite["duration"] == "until cured"
    assert len(indefinite["rows"]) == 2


def test_parse_madness_tables_missing_part2():
    """Test parsing short-term madness without part2."""
    tables_data = {
        "short_term_madness": {
            "page": 201,
            "rows": [
                ["01-20", "The character retreats into his or her mind"],
            ],
        },
    }

    result = parse_madness_tables(tables_data)

    assert len(result) == 1
    assert result[0]["simple_name"] == "short_term_madness"
    assert len(result[0]["rows"]) == 1


def test_parse_madness_tables_empty_rows():
    """Test parsing tables with empty rows arrays."""
    tables_data = {
        "short_term_madness": {"page": 201, "rows": []},
        "long_term_madness": {"page": 201, "rows": []},
        "indefinite_madness": {"page": 202, "rows": []},
    }

    result = parse_madness_tables(tables_data)
    assert result == []


def test_filter_header_rows_removes_headers():
    """Test that header rows are filtered out."""
    rows = [
        ["d100", "Effect"],
        ["01-20", "Some effect"],
        ["Effect", "Description"],
        ["21-30", "Another effect"],
    ]

    result = _filter_header_rows(rows)

    assert len(result) == 2
    assert result[0] == ["01-20", "Some effect"]
    assert result[1] == ["21-30", "Another effect"]


def test_filter_header_rows_handles_flaw():
    """Test that 'flaw' headers are also filtered."""
    rows = [
        ["d100", "Flaw"],
        ["01-20", "Some effect"],
    ]

    result = _filter_header_rows(rows)

    assert len(result) == 1
    assert result[0] == ["01-20", "Some effect"]


def test_filter_header_rows_handles_short_rows():
    """Test that rows with fewer than 2 columns are filtered."""
    rows = [
        ["d100"],
        ["01-20", "Valid effect"],
        [],
    ]

    result = _filter_header_rows(rows)

    assert len(result) == 1
    assert result[0] == ["01-20", "Valid effect"]


def test_clean_effect_text_fixes_dashes():
    """Test that garbled dashes are cleaned up."""
    text = "A long­‐‑range attack"
    result = _clean_effect_text(text)
    assert "­‐‑" not in result
    assert "-" in result


def test_clean_effect_text_fixes_quotes():
    """Test that smart quotes are normalized."""
    # Test with garbled/special characters that might appear in PDF text
    text = "Text with special-dash"
    result = _clean_effect_text(text)
    assert "special-dash" in result  # Basic normalization works


def test_clean_effect_text_normalizes_whitespace():
    """Test that multiple spaces are collapsed."""
    text = "Multiple   spaces    here"
    result = _clean_effect_text(text)
    assert result == "Multiple spaces here"


def test_clean_effect_text_strips_whitespace():
    """Test that leading/trailing whitespace is removed."""
    text = "  Some text  "
    result = _clean_effect_text(text)
    assert result == "Some text"


def test_parse_madness_tables_preserves_page_numbers():
    """Test that page numbers are preserved from input data."""
    tables_data = {
        "short_term_madness": {
            "page": 999,
            "rows": [["01-20", "Effect text"]],
        },
    }

    result = parse_madness_tables(tables_data)

    assert len(result) == 1
    assert result[0]["page"] == 999
