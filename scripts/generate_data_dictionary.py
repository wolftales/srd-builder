#!/usr/bin/env python3
"""Generate DATA_DICTIONARY.md from JSON schemas.

This script automatically generates API-style documentation from the schema files,
similar to Swagger/OpenAPI documentation. It extracts field definitions, types,
patterns, and descriptions to create a comprehensive data dictionary.

Usage:
    python scripts/generate_data_dictionary.py
    python scripts/generate_data_dictionary.py --output docs/DATA_DICTIONARY.md
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def get_schema_version() -> str:
    """Extract schema version from constants."""
    constants_file = Path("src/srd_builder/constants.py")
    content = constants_file.read_text()
    for line in content.splitlines():
        if line.startswith("SCHEMA_VERSION"):
            return line.split('"')[1]
    return "unknown"


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load and parse a JSON schema file."""
    return json.loads(schema_path.read_text())


def format_type(type_def: Any) -> str:
    """Format JSON schema type definition as readable string."""
    if isinstance(type_def, str):
        return f"`{type_def}`"
    elif isinstance(type_def, list):
        return " or ".join(f"`{t}`" for t in type_def)
    return "`any`"


def format_pattern(pattern: str) -> str:
    """Format regex pattern for documentation."""
    return f"`{pattern}`"


def get_field_constraints(prop_def: dict[str, Any]) -> list[str]:
    """Extract validation constraints from property definition."""
    constraints = []

    if "minLength" in prop_def:
        constraints.append(f"min length: {prop_def['minLength']}")
    if "maxLength" in prop_def:
        constraints.append(f"max length: {prop_def['maxLength']}")
    if "minimum" in prop_def:
        constraints.append(f"min: {prop_def['minimum']}")
    if "maximum" in prop_def:
        constraints.append(f"max: {prop_def['maximum']}")
    if "enum" in prop_def:
        values = ", ".join(f"`{v}`" for v in prop_def["enum"])
        constraints.append(f"allowed: {values}")
    if "pattern" in prop_def:
        constraints.append(f"pattern: {format_pattern(prop_def['pattern'])}")
    if "uniqueItems" in prop_def and prop_def["uniqueItems"]:
        constraints.append("unique items")
    if "minItems" in prop_def:
        constraints.append(f"min items: {prop_def['minItems']}")
    if "maxItems" in prop_def:
        constraints.append(f"max items: {prop_def['maxItems']}")

    return constraints


def document_property(  # noqa: C901
    name: str, prop_def: dict[str, Any], required: bool, indent: int = 0
) -> list[str]:
    """Generate documentation lines for a single property."""
    lines = []
    prefix = "  " * indent

    # Property header
    req_badge = " **(required)**" if required else " *(optional)*"
    lines.append(f"{prefix}### `{name}`{req_badge}")
    lines.append("")

    # Type information
    if "type" in prop_def:
        type_str = format_type(prop_def["type"])
        lines.append(f"{prefix}**Type:** {type_str}")
    elif "oneOf" in prop_def:
        lines.append(f"{prefix}**Type:** One of:")
        for i, option in enumerate(prop_def["oneOf"], 1):
            opt_type = format_type(option.get("type", "object"))
            lines.append(f"{prefix}  {i}. {opt_type}")
    elif "anyOf" in prop_def:
        lines.append(f"{prefix}**Type:** Any of:")
        for i, option in enumerate(prop_def["anyOf"], 1):
            opt_type = format_type(option.get("type", "object"))
            lines.append(f"{prefix}  {i}. {opt_type}")

    # Array items type
    if prop_def.get("type") == "array" and "items" in prop_def:
        items_type = format_type(prop_def["items"].get("type", "object"))
        lines.append(f"{prefix}**Items:** {items_type}")

    # Constraints
    constraints = get_field_constraints(prop_def)
    if constraints:
        lines.append(f"{prefix}**Constraints:** {', '.join(constraints)}")

    # Description
    if "description" in prop_def:
        lines.append(f"{prefix}**Description:** {prop_def['description']}")

    # Examples
    if "examples" in prop_def:
        lines.append(f"{prefix}**Examples:**")
        for example in prop_def["examples"]:
            lines.append(f"{prefix}  - `{json.dumps(example)}`")

    lines.append("")
    return lines


def document_schema(schema_name: str, schema: dict[str, Any]) -> list[str]:
    """Generate documentation for a complete schema."""
    lines = []

    # Schema header
    lines.append(f"## {schema_name.replace('_', ' ').title()}")
    lines.append("")

    if "description" in schema:
        lines.append(schema["description"])
        lines.append("")

    # Required fields
    required_fields = set(schema.get("required", []))

    # Document properties
    properties = schema.get("properties", {})
    if properties:
        lines.append("### Fields")
        lines.append("")

        # Sort: required first, then alphabetically within each group
        sorted_props = sorted(properties.items(), key=lambda x: (x[0] not in required_fields, x[0]))

        for prop_name, prop_def in sorted_props:
            is_required = prop_name in required_fields
            lines.extend(document_property(prop_name, prop_def, is_required))

    lines.append("---")
    lines.append("")
    return lines


def generate_universal_fields_section() -> list[str]:
    """Generate documentation for universal fields (shared across all schemas)."""
    lines = [
        "## Universal Fields",
        "",
        "These fields appear consistently across all entity types:",
        "",
        "### `id` **(required)**",
        "",
        "**Type:** `string`",
        "**Pattern:** `<entity_type>:<normalized_name>`",
        "**Examples:** `monster:adult_red_dragon`, `item:longsword`, `spell:fireball`, `lineage:dwarf`",
        "**Description:** Stable, globally unique identifier for cross-referencing. Formed by namespacing the entity type with the normalized name.",
        "",
        "### `simple_name` **(required)**",
        "",
        "**Type:** `string`",
        "**Pattern:** `^[a-z0-9_]+$` (lowercase alphanumeric + underscores)",
        "**Examples:** `adult_red_dragon`, `longsword`, `fireball`, `dwarf`",
        "**Description:** Human-readable identifier without namespace prefix. Used for indexing, search, and sorting.",
        "",
        "### `name` **(required)**",
        "",
        "**Type:** `string`",
        '**Description:** Display name from SRD (e.g., "Adult Red Dragon", "Longsword", "Fireball", "Dwarf"). Preserves original capitalization and spacing.',
        "",
        "### `aliases` *(optional)*",
        "",
        "**Type:** `array` of `string`",
        "**Constraints:** unique items",
        '**Description:** Alternative names or search terms for this entity. Used for flexible lookups (e.g., "flask" and "tankard" for "Flask or tankard").',
        "**Added:** Schema v1.3.0",
        "",
        "---",
        "",
    ]
    return lines


def generate_data_dictionary() -> str:
    """Generate complete DATA_DICTIONARY.md content."""
    schema_version = get_schema_version()
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        "# Data Dictionary",
        "",
        "**Auto-generated API documentation for SRD dataset schemas**",
        "",
        f"**Schema Version:** {schema_version}",
        f"**Generated:** {today}",
        "",
        "---",
        "",
        "## Purpose",
        "",
        "This document provides comprehensive field-level documentation for all SRD dataset schemas. ",
        "It's automatically generated from the JSON schema files to ensure accuracy and consistency.",
        "",
        "Like Swagger/OpenAPI documentation, this dictionary describes:",
        "",
        "- **Field names and types** - What each field is called and what data it contains",
        "- **Validation rules** - Patterns, constraints, and allowed values",
        "- **Required vs optional** - Which fields must be present",
        "- **Descriptions** - What each field means and how it's used",
        "",
        "---",
        "",
    ]

    # Add universal fields section
    lines.extend(generate_universal_fields_section())

    # Process each schema
    schemas_dir = Path("schemas")
    schema_files = sorted(schemas_dir.glob("*.schema.json"))

    for schema_file in schema_files:
        schema_name = schema_file.stem.replace(".schema", "")
        try:
            schema = load_schema(schema_file)
            lines.extend(document_schema(schema_name, schema))
        except Exception as e:
            print(f"Warning: Failed to process {schema_file}: {e}")
            continue

    # Footer
    lines.extend(
        [
            "## Version History",
            "",
            "- **v1.3.0** (2025-11-02): Added `aliases` field to all entity schemas, added `lineage` schema",
            "- **v1.2.0** (2025-10-30): Added `tables` schema with structured reference tables",
            "- **v1.1.0** (2024): Initial schema standardization",
            "",
            "---",
            "",
            "## Schema Files",
            "",
            "The authoritative schema definitions are located in `schemas/`:",
            "",
        ]
    )

    for schema_file in schema_files:
        lines.append(f"- `{schema_file.name}`")

    lines.extend(
        [
            "",
            "For implementation details and examples, see `docs/SCHEMAS.md`.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate DATA_DICTIONARY.md from JSON schemas")
    parser.add_argument(
        "--output",
        "-o",
        default="docs/DATA_DICTIONARY.md",
        help="Output file path",
    )

    args = parser.parse_args()
    output_path = Path(args.output)

    print("Generating data dictionary from schemas/...")
    content = generate_data_dictionary()

    output_path.write_text(content, encoding="utf-8")
    print(f"✓ Generated {output_path}")
    print(f"  {len(content.splitlines())} lines")


if __name__ == "__main__":
    main()
