"""Unified table extraction engine.

This module contains pattern-based extraction engines that interpret table configs
from table_metadata.py. The config's pattern_type field routes to the appropriate
extraction engine, eliminating the need for table-specific parsing functions.

Design Philosophy:
- Metadata shapes extraction logic (not code)
- One engine per pattern type (not per table)
- All table-specific configuration in table_metadata.py

Supported Pattern Types:
- standard_grid: PyMuPDF auto-detected grid tables
- split_column: Side-by-side sub-tables within same page region
- multipage_text_region: Text extraction across multiple page regions
- text_region: Text extraction from single page region
- calculated: Generated from formula/lookup
- reference: Static hardcoded data (fallback)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RawTable:
    """Raw extracted table data before normalization."""

    table_id: str
    simple_name: str
    page: int | list[int]
    headers: list[str]
    rows: list[list[str | int | float]]
    extraction_method: str
    section: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] | None = None
    chapter: str | None = None  # Chapter/section where table appears in SRD
    confirmed: bool = False  # Whether extraction has been verified working
    source: str | None = None  # Data provenance: srd, derived, convenience, reference, custom


def extract_by_config(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None = None,
    pdf_path: str | None = None,
) -> RawTable:
    """Universal table extraction based on config's pattern_type.

    Routes to appropriate extraction engine based on pattern_type field:
    - calculated → _extract_calculated()
    - reference → _extract_reference()
    - split_column → _extract_split_column()
    - text_region → _extract_text_region()
    - multipage_text_region → _extract_multipage_text_region()
    - standard_grid → _extract_standard_grid()

    Args:
        table_id: Unique table identifier (e.g., "table:experience_by_cr")
        simple_name: Simple name (e.g., "experience_by_cr")
        page: Source page number(s)
        config: Table configuration dict from table_metadata.py
        section: Optional section name
        pdf_path: Path to PDF file (required for PDF extraction patterns)

    Returns:
        RawTable with extracted data
    """
    pattern_type = config.get("pattern_type")

    if not pattern_type:
        raise ValueError(f"Config for {simple_name} missing required 'pattern_type' field")

    # Route to appropriate extraction engine
    if pattern_type == "calculated":
        return _extract_calculated(table_id, simple_name, page, config, section)

    elif pattern_type == "reference":
        return _extract_reference(table_id, simple_name, page, config, section)

    elif pattern_type == "split_column":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_split_column(table_id, simple_name, page, config, section, pdf_path)

    elif pattern_type == "text_region":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_text_region(table_id, simple_name, page, config, section, pdf_path)

    elif pattern_type == "multipage_text_region":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_multipage_text_region(
            table_id, simple_name, page, config, section, pdf_path
        )

    elif pattern_type == "standard_grid":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_standard_grid(table_id, simple_name, page, config, section, pdf_path)

    elif pattern_type == "legacy_parser":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_legacy_parser(table_id, simple_name, page, config, section, pdf_path)

    else:
        raise ValueError(f"Unknown pattern_type '{pattern_type}' for {simple_name}")


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACTION ENGINES - One per pattern type
# ═══════════════════════════════════════════════════════════════════════════


def _extract_calculated(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
) -> RawTable:
    """Extract calculated table (formula or lookup based).

    Config structure:
        {
            "pattern_type": "calculated",
            "source": "derived" | "convenience",
            "calculation": {
                "method": "formula" | "lookup",
                "formula": lambda x: ...,  # if method=formula
                "data": {...},              # if method=lookup
                "range": range(...),
            },
            "headers": [...],
            "notes": "..."
        }
    """
    calc_config = config["calculation"]
    method = calc_config["method"]

    if method == "formula":
        rows = _generate_formula_rows(calc_config)
    elif method == "lookup":
        rows = _generate_lookup_rows(calc_config)
    else:
        raise ValueError(f"Unknown calculation method '{method}' for {simple_name}")

    source = config.get("source", "calculated")
    notes = config.get("notes", f"Calculated table [source: {source}]")
    chapter = config.get("chapter")
    confirmed = config.get("confirmed", False)

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=config["headers"],
        rows=rows,
        extraction_method="calculated",
        section=section,
        notes=notes,
        chapter=chapter,
        confirmed=confirmed,
        source=source,
    )


def _extract_reference(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
) -> RawTable:
    """Extract reference table (static hardcoded data).

    Config structure:
        {
            "pattern_type": "reference",
            "source": "reference" | "srd",
            "headers": [...],
            "rows": [[...], [...]],
            "notes": "...",
            "use_legacy_data": "CLASS_PROGRESSIONS"  # Optional: fallback to reference_data.py
        }
    """
    source = config.get("source", "reference")
    notes = config.get("notes", f"Reference data from SRD 5.1 [source: {source}]")

    # Check if we need to load from legacy reference_data.py
    if "use_legacy_data" in config:
        from . import reference_data

        legacy_source = config["use_legacy_data"]
        if legacy_source == "CLASS_PROGRESSIONS":
            # Strip _progression suffix to get the class name
            class_name = simple_name.replace("_progression", "")
            legacy_data = reference_data.CLASS_PROGRESSIONS.get(class_name)
            if not legacy_data:
                raise ValueError(f"Table {class_name} not found in CLASS_PROGRESSIONS")

            chapter = config.get("chapter")
            confirmed = config.get("confirmed", False)

            return RawTable(
                table_id=table_id,
                simple_name=simple_name,
                page=page,
                headers=legacy_data["headers"],
                rows=legacy_data["rows"],
                extraction_method="reference",
                section=section,
                notes=notes,
                chapter=chapter,
                confirmed=confirmed,
                source=source,
            )

    # Standard reference with headers/rows in config
    chapter = config.get("chapter")
    confirmed = config.get("confirmed", False)

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=config["headers"],
        rows=config["rows"],
        extraction_method="reference",
        section=section,
        notes=notes,
        chapter=chapter,
        confirmed=confirmed,
        source=source,
    )


def _extract_split_column(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
    pdf_path: str,
) -> RawTable:
    """Extract split-column table (side-by-side sub-tables in same region).

    Config structure:
        {
            "pattern_type": "split_column",
            "source": "srd",
            "pages": [258],
            "headers": ["Challenge Rating", "XP"],
            "regions": [
                {"x_min": 0, "x_max": 130, "y_min": 445, "y_max": 665},
                {"x_min": 130, "x_max": 250, "y_min": 445, "y_max": 665},
            ],
            "transformations": {...},
            "special_cases": [...]
        }
    """
    import pymupdf

    from .text_parser_utils import group_words_by_y

    pages = config["pages"]
    regions = config["regions"]
    headers = config["headers"]
    transformations = config.get("transformations", {})
    special_cases = config.get("special_cases", [])

    doc = pymupdf.open(pdf_path)
    page_obj = doc[pages[0] - 1]
    words = page_obj.get_text("words")
    doc.close()

    all_rows: list[list[str | int | float]] = []

    # Process each region (sub-table)
    for region in regions:
        x_min = region.get("x_min", 0)
        x_max = region.get("x_max", 999999)
        y_min = region.get("y_min", 0)
        y_max = region.get("y_max", 999999)

        # Filter words to region
        region_words = [w for w in words if x_min <= w[0] < x_max and y_min <= w[1] <= y_max]

        # Group by Y-coordinate
        rows_dict = group_words_by_y(region_words)

        # Parse rows
        for _y_pos, row_words in sorted(rows_dict.items()):
            row_text = " ".join([text for x, text in sorted(row_words, key=lambda w: w[0])])

            # Skip header rows
            if any(h.lower() in row_text.lower() for h in headers):
                continue

            words_list = row_text.split()
            if len(words_list) >= len(headers):
                parsed_row = _parse_row(words_list, headers, transformations, special_cases)
                if parsed_row:
                    all_rows.append(parsed_row)

    source = config.get("source", "srd")
    chapter = config.get("chapter")
    confirmed = config.get("confirmed", False)
    notes = f"Extracted from PDF using split_column pattern [source: {source}]"

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=headers,
        rows=all_rows,
        extraction_method="text_parsed",
        section=section,
        notes=notes,
        chapter=chapter,
        confirmed=confirmed,
        source=source,
    )


def _extract_text_region(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
    pdf_path: str,
) -> RawTable:
    """Extract text-region table (single page region).

    Extracts table from a defined rectangular region on a single page.
    Handles cases where PyMuPDF splits tables into multiple 1-row tables.

    Config requirements:
        - pages: [int] - Single page number
        - headers: list[str] - Column headers
        - region: dict with x_min, x_max, y_min, y_max coordinates
    """
    import pymupdf as fitz

    pages = config["pages"]
    if not isinstance(pages, list) or len(pages) != 1:
        raise ValueError(f"{simple_name}: text_region requires single page, got {pages}")

    page_num = pages[0]
    headers = config["headers"]
    region = config["region"]

    doc = fitz.open(pdf_path)
    page_obj = doc[page_num - 1]  # Convert to 0-indexed

    # Find all tables within the specified region
    tables = page_obj.find_tables()
    rows: list[list[str | int | float]] = []

    # Collect all table rows within the region
    for table in tables:
        bbox = table.bbox
        # Check if table is within our region
        if (
            region["x_min"] <= bbox[0] <= region["x_max"]
            and region["y_min"] <= bbox[1] <= region["y_max"]
        ):
            extracted = table.extract()
            rows.extend(extracted)

    doc.close()

    # Create RawTable
    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page_num,
        headers=headers,
        rows=rows,
        extraction_method="text_region",
        section=section,
        chapter=config.get("chapter"),
        confirmed=config.get("confirmed", False),
        source=config.get("source", "srd"),
    )


def _extract_multipage_text_region(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
    pdf_path: str,
) -> RawTable:
    """Extract multipage text-region table (across page boundaries).

    Used for tables like food_drink_lodging that span multiple pages.
    """
    # TODO: Implement once we have more examples
    raise NotImplementedError(
        f"multipage_text_region pattern not yet implemented for {simple_name}"
    )


def _extract_standard_grid(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
    pdf_path: str,
) -> RawTable:
    """Extract standard grid table using PyMuPDF auto-detection.

    Config structure:
        {
            "pattern_type": "standard_grid",
            "source": "srd",
            "pages": [63, 64],
            "auto_detect": True,
            "header_hints": ["armor", "cost", "ac"]
        }
    """
    # TODO: Implement PyMuPDF auto-detection with header hints
    raise NotImplementedError(f"standard_grid pattern not yet implemented for {simple_name}")


def _extract_legacy_parser(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
    pdf_path: str,
) -> RawTable:
    """Extract table using legacy parser function from text_table_parser.py.

    This is a temporary pattern during migration. Gradually replace with generic engines.

    Config structure:
        {
            "pattern_type": "legacy_parser",
            "source": "srd",
            "pages": [73, 74],
            "parser": "parse_food_drink_lodging_table"
        }
    """
    from . import text_table_parser

    parser_name = config["parser"]
    pages = config["pages"]

    # Get parser function by name
    if not hasattr(text_table_parser, parser_name):
        raise ValueError(f"Parser function '{parser_name}' not found in text_table_parser.py")

    parser_func = getattr(text_table_parser, parser_name)
    result = parser_func(pdf_path, pages)

    source = config.get("source", "srd")
    chapter = config.get("chapter")
    confirmed = config.get("confirmed", False)
    notes = f"Extracted via legacy parser {parser_name} [source: {source}]"

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=result["headers"],
        rows=result["rows"],
        extraction_method="text_parsed",
        section=section,
        notes=notes,
        metadata=result.get("categories"),
        chapter=chapter,
        confirmed=confirmed,
        source=source,
    )


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


def _parse_row(
    words_list: list[str],
    headers: list[str],
    transformations: dict[str, Any],
    special_cases: list[dict[str, Any]],
) -> list[str | int | float] | None:
    """Parse a row of words into typed values based on config.

    Args:
        words_list: List of words from PDF
        headers: Column headers
        transformations: Dict of column transformations
        special_cases: List of special case rules

    Returns:
        Parsed row or None if parsing fails
    """
    if len(words_list) < len(headers):
        return None

    parsed_row: list[str | int | float] = []

    for i, header in enumerate(headers):
        if i >= len(words_list):
            break

        value = words_list[i]

        # Apply transformations
        if header in transformations:
            trans = transformations[header]

            if trans.get("remove_commas"):
                value = value.replace(",", "")

            if trans.get("cast") == "int":
                try:
                    value = int(value)  # type: ignore[assignment]
                except ValueError:
                    pass

        parsed_row.append(value)

    return parsed_row if parsed_row else None


def _generate_formula_rows(config: dict[str, Any]) -> list[list[str | int | float]]:
    """Generate rows from formula config.

    Example config:
        {
            "formula": lambda x: x * 15,
            "range": range(1, 31),
            "headers": ["Strength", "Capacity"],
            "format": lambda val: f"{val} lbs"  # optional
        }
    """
    formula = config["formula"]
    value_range = config["range"]
    format_fn = config.get("format_modifier") or config.get("format", lambda x: x)

    rows: list[list[str | int | float]] = []
    for val in value_range:
        result = formula(val)
        formatted_result = format_fn(result)
        rows.append([val, formatted_result])

    return rows


def _generate_lookup_rows(config: dict[str, Any]) -> list[list[str | int | float]]:
    """Generate rows from lookup dict config.

    Example config:
        {
            "data": {
                range(1, 5): "+2",
                range(5, 9): "+3",
                ...
            },
            "headers": ["Level", "Bonus"]
        }
    """
    lookup = config["data"]
    rows: list[list[str | int | float]] = []

    # Build lookup by iterating ranges
    for range_obj, value in lookup.items():
        for key in range_obj:
            rows.append([key, value])

    return rows
