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

    # Generate id and simple_name using shared utility.
    # IDs are namespaced by parent section (subcategory if present, else
    # category) — `rule:{section}/{name}` — so headings reused across
    # SRD sections (e.g. "Strength" under Ability Checks vs Using Each
    # Ability) get distinct IDs. Mirrors how tables disambiguate by category.
    cleaned_name = clean_text(name)
    simple_name = normalize_id(cleaned_name)
    section = rule.get("subcategory") or category
    section_simple = normalize_id(clean_text(section))
    rule_id = f"rule:{section_simple}/{simple_name}"

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
        "source": rule["source"],
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


def dedupe_rule_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Drop exact duplicate rule records and disambiguate remaining collisions.

    The SRD layout exposes two kinds of rule-id collisions that survive
    section-namespacing:

    1. Byte-identical duplicates extracted twice (e.g. Time/Movement/Speed
       headings reused across the Adventuring overview and its movement
       subsection). Drop the second occurrence by `(id, page, tuple(text))`.

    2. Distinct subsections that share a grandparent the parser cannot
       see (e.g. "Attack Rolls and Damage" appears under both Strength
       and Dexterity inside the Using Each Ability subsection; the parser
       only tracks immediate parent). Append a 1-based ordinal suffix to
       `id` and `simple_name` for the 2nd, 3rd, ... occurrences so every
       record keeps a stable unique id without losing data.
    """
    # Pass 1: drop byte-identical duplicates.
    seen: set[tuple[str, int, tuple[str, ...]]] = set()
    deduped: list[dict[str, Any]] = []
    for rec in records:
        key = (rec["id"], int(rec.get("page", 0) or 0), tuple(rec.get("text", []) or ()))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rec)

    # Pass 2: ordinal-suffix any remaining id collisions.
    id_counts: dict[str, int] = {}
    for rec in deduped:
        id_counts[rec["id"]] = id_counts.get(rec["id"], 0) + 1
    if any(c > 1 for c in id_counts.values()):
        seen_id: dict[str, int] = {}
        for rec in deduped:
            rid = rec["id"]
            if id_counts[rid] > 1:
                n = seen_id.get(rid, 0) + 1
                seen_id[rid] = n
                if n > 1:
                    rec["id"] = f"{rid}_{n}"
                    if "simple_name" in rec:
                        rec["simple_name"] = f"{rec['simple_name']}_{n}"
    return deduped


def main() -> int:
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
    cleaned_rules = dedupe_rule_records([clean_rule_record(rule) for rule in parsed_rules])

    # Write to stdout
    print(json.dumps(cleaned_rules, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
