#!/usr/bin/env python3
"""Rules postprocessing for SRD 5.1.

Normalizes parsed rule records following the modular pattern.
Uses shared utilities for ID generation and text cleanup.

This module implements the POSTPROCESS stage:
- Generates id (rule:*) and simple_name
- Polishes text arrays
- Assigns final categories/subcategories
- Detects cross-references
- Uses normalize_id() and polish_text() from shared utilities
"""

from __future__ import annotations

from typing import Any

from .ids import normalize_id
from .text import clean_text, polish_text


def clean_rule_record(rule: dict[str, Any]) -> dict[str, Any]:
    """Clean and normalize a single rule record.

    POSTPROCESS STAGE: Normalization only (uses shared utilities).

    Args:
        rule: Unnormalized rule dict from parse_rules()

    Returns:
        Normalized rule dict with id, simple_name, polished text
    """
    name = rule.get("name", "")
    category = rule.get("category", "")

    if not name:
        raise ValueError("Rule record missing 'name' field")
    if not category:
        raise ValueError(f"Rule '{name}' missing 'category' field")

    # Generate id and simple_name using shared utility
    # Clean name first to remove control characters
    cleaned_name = clean_text(name)
    simple_name = normalize_id(cleaned_name)
    rule_id = f"rule:{simple_name}"

    # Polish text arrays using shared utility
    text = rule.get("text", [])
    polished_text = []
    for paragraph in text:
        if not paragraph.strip():
            continue
        # First clean control characters, then polish formatting
        cleaned = clean_text(paragraph)
        polished = polish_text(cleaned)
        if polished:
            polished_text.append(polished)

    # Build normalized record
    cleaned_record: dict[str, Any] = {
        "id": rule_id,
        "name": cleaned_name,
        "simple_name": simple_name,
        "category": clean_text(category),
        "page": rule.get("page", 0),
        "source": rule.get("source", "SRD 5.1"),
        "text": polished_text,
    }

    # Optional fields (only include if present and non-empty)
    if rule.get("subcategory"):
        cleaned_record["subcategory"] = clean_text(rule["subcategory"])

    if rule.get("parent_id"):
        cleaned_record["parent_id"] = rule["parent_id"]

    if rule.get("summary"):
        cleaned_record["summary"] = polish_text(clean_text(rule["summary"]))

    if rule.get("aliases"):
        cleaned_record["aliases"] = sorted(set(clean_text(a) for a in rule["aliases"]))

    if rule.get("tags"):
        cleaned_record["tags"] = sorted(set(rule["tags"]))

    # Cross-reference fields (only include if non-empty)
    for ref_field in [
        "related_conditions",
        "related_spells",
        "related_features",
        "related_tables",
    ]:
        if rule.get(ref_field):
            cleaned_record[ref_field] = sorted(set(rule[ref_field]))

    return cleaned_record


def main():
    """Command-line entry point for testing."""
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m srd_builder.postprocess.rules <parsed_rules.json>")
        return 1

    import pathlib

    parsed_path = pathlib.Path(sys.argv[1])
    parsed_rules = json.loads(parsed_path.read_text(encoding="utf-8"))

    # Process each rule
    cleaned_rules = [clean_rule_record(rule) for rule in parsed_rules]

    # Write to stdout
    print(json.dumps(cleaned_rules, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
