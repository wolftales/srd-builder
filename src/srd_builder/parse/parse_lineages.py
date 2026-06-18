"""Parse lineage data from extracted records into validated lineage records.

GUARDRAILS: Pure parsing/mapping only (no I/O/logging)
BOUNDARIES: Transforms extracted lineage records → structured records with
            extraction metadata. Input is the ``lineages`` list produced by
            ``srd_builder.extract.datasets.extract_lineages.extract_lineages``.
"""

from __future__ import annotations

from typing import Any


def parse_lineages(lineage_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Parse all lineages from extracted lineage data.

    Args:
        lineage_data: ``lineages`` list from
            :func:`extract_lineages.extract_lineages`. Each entry carries
            ``name``, ``simple_name``, ``page``, ``ability_modifiers``,
            ``size``, ``speed``, ``languages``, ``traits`` and optional
            ``age``/``alignment``/``size_description``/``ability_modifier_note``/
            ``subraces``.

    Returns:
        List of lineage records with all subraces expanded as separate
        entries. Each record includes ``extraction_metadata`` for
        provenance.
    """
    lineages: list[dict[str, Any]] = []

    for entry in lineage_data:
        # Build base lineage record
        lineage = _build_lineage_record(entry)
        lineages.append(lineage)

        # Build subrace records if present
        if entry.get("subraces"):
            for subrace_data in entry["subraces"]:
                subrace = _build_subrace_record(entry, subrace_data)
                lineages.append(subrace)

    return lineages


def _build_lineage_record(data: dict[str, Any]) -> dict[str, Any]:
    """Build a complete lineage record from target data.

    Args:
        data: Lineage entry from extract_lineages

    Returns:
        Fully structured lineage record with metadata
    """
    simple_name = data["simple_name"]

    record: dict[str, Any] = {
        "id": f"lineage:{simple_name}",
        "simple_name": simple_name,
        "name": data["name"],
        "size": data["size"],
        "speed": data["speed"],
        "ability_modifiers": data["ability_modifiers"],
        "languages": data["languages"],
        "traits": data["traits"],
        "extraction_metadata": {
            "source_pages": [data["page"]],
            "section": "races",
            "extraction_notes": f"{data['name']} from SRD 5.1",
        },
    }

    # Optional fields
    if "ability_modifier_note" in data:
        record["ability_modifier_note"] = data["ability_modifier_note"]

    if "age" in data:
        record["age"] = data["age"]

    if "alignment" in data:
        record["alignment"] = data["alignment"]

    if "size_description" in data:
        record["size_description"] = data["size_description"]

    if data.get("subraces"):
        record["subraces"] = data["subraces"]

    # Add tables_referenced if any traits reference tables
    tables_referenced = _extract_table_references(data["traits"])
    if tables_referenced:
        record["tables_referenced"] = tables_referenced

    return record


def _build_subrace_record(
    parent_data: dict[str, Any], subrace_data: dict[str, Any]
) -> dict[str, Any]:
    """Build a separate record for a subrace.

    Args:
        parent_data: Parent lineage data
        subrace_data: Subrace-specific data

    Returns:
        Complete subrace record that combines parent + subrace traits
    """
    simple_name = subrace_data["simple_name"]
    parent_simple_name = parent_data["simple_name"]

    # Merge ability modifiers (parent + subrace)
    combined_abilities = {**parent_data["ability_modifiers"]}
    for ability, bonus in subrace_data["ability_modifiers"].items():
        combined_abilities[ability] = combined_abilities.get(ability, 0) + bonus

    # Merge traits (parent + subrace)
    combined_traits = parent_data["traits"] + subrace_data["traits"]

    record: dict[str, Any] = {
        "id": f"lineage:{simple_name}",
        "simple_name": simple_name,
        "name": subrace_data["name"],
        "parent_lineage": f"lineage:{parent_simple_name}",
        "size": parent_data["size"],
        "speed": parent_data["speed"],
        "ability_modifiers": combined_abilities,
        "languages": parent_data["languages"],
        "traits": combined_traits,
        "extraction_metadata": {
            "source_pages": [parent_data["page"]],
            "section": "races",
            "extraction_notes": (f"{subrace_data['name']} subrace of {parent_data['name']}"),
        },
    }

    # Optional parent fields
    if "age" in parent_data:
        record["age"] = parent_data["age"]

    if "alignment" in parent_data:
        record["alignment"] = parent_data["alignment"]

    if "size_description" in parent_data:
        record["size_description"] = parent_data["size_description"]

    # Add tables_referenced if any traits reference tables
    tables_referenced = _extract_table_references(combined_traits)
    if tables_referenced:
        record["tables_referenced"] = tables_referenced

    return record


def _extract_table_references(traits: list[dict[str, Any]]) -> list[str]:
    """Extract table IDs referenced by traits.

    Args:
        traits: List of trait dictionaries

    Returns:
        Sorted list of unique table IDs
    """
    table_ids = set()

    for trait in traits:
        if "references_table" in trait:
            # Note: draconic_ancestry table not in v0.7.0 tables.json
            # Will need to be added or handled specially
            table_ids.add(f"table:{trait['references_table']}")

    return sorted(table_ids)
