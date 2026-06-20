"""Unified table extraction engine.

This module contains pattern-based extraction engines that interpret table configs
from extraction_metadata.py. The config's pattern_type field routes to the appropriate
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
- prose_section: Named prose sections (conditions, diseases, equipment descriptions)
- calculated: Generated from formula/lookup
- reference: Static hardcoded data (fallback)
"""

from __future__ import annotations

import logging
import re
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
    - prose_section → _extract_prose_section()
    - standard_grid → _extract_standard_grid()

    Args:
        table_id: Unique table identifier (e.g., "table:experience_by_cr")
        simple_name: Simple name (e.g., "experience_by_cr")
        page: Source page number(s)
        config: Table configuration dict from extraction_metadata.py
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

    elif pattern_type == "prose_section":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_prose_section(table_id, simple_name, page, config, section, pdf_path)

    elif pattern_type == "standard_grid":
        if not pdf_path:
            raise ValueError(f"PDF extraction for {simple_name} requires pdf_path parameter")
        return _extract_standard_grid(table_id, simple_name, page, config, section, pdf_path)

    else:
        raise ValueError(f"Unknown pattern_type '{pattern_type}' for {simple_name}")


# ═══════════════════════════════════════════════════════════════════════════
# RECORD-SHAPED EXTRACTION (sibling to extract_by_config)
# ═══════════════════════════════════════════════════════════════════════════
#
# extract_by_config() returns RawTable (row/column shape). Some extractors
# produce lists of dict records instead (per-item, per-feature, per-monster).
# extract_records_by_config() is the routing entry point for those.


def extract_records_by_config(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Record-shaped extraction (lists of dicts) based on config's pattern_type.

    Sibling to extract_by_config(); used by pattern types that emit per-record
    dicts rather than tabular rows.

    Routes:
    - font_fingerprint_walk → _extract_font_fingerprint_walk()
    """
    pattern_type = config.get("pattern_type")
    if not pattern_type:
        raise ValueError("Record-shaped config missing required 'pattern_type' field")

    if pattern_type == "font_fingerprint_walk":
        return _extract_font_fingerprint_walk(pdf_path, pages, config)

    raise ValueError(
        f"Unknown record-shaped pattern_type '{pattern_type}' (known: font_fingerprint_walk)"
    )


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
        }
    """
    source = config.get("source", "reference")
    notes = config.get("notes", f"Reference data from SRD 5.1 [source: {source}]")
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


def _build_category_metadata(
    rows: list[list[str | int | float]], headers: list[str]
) -> dict[str, Any]:
    """Build category metadata from extracted rows.

    Categories are detected when all numeric columns contain only "—" (em-dash).
    The first column contains the category name.

    Returns:
        Dict with "categories" key mapping category names to item lists:
        {
            "categories": {
                "Category Name": {
                    "row_index": 0,
                    "items": [{"name": "Item1", "row_index": 1}, ...]
                }
            }
        }
    """
    categories: dict[str, dict[str, Any]] = {}
    current_category: str | None = None

    for i, row in enumerate(rows):
        # Category detection: all columns except first are "—" or empty
        is_category = all(str(cell).strip() in ("—", "") for cell in row[1:])

        if is_category and row[0]:
            # This is a category header
            category_name = str(row[0]).strip()
            current_category = category_name
            categories[current_category] = {"row_index": i, "items": []}
        elif current_category and row[0]:
            # This is an item under the current category
            item_name = str(row[0]).strip()
            categories[current_category]["items"].append({"name": item_name, "row_index": i})

    return {"categories": categories} if categories else {}


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
            "special_cases": [...],
            "detect_categories": True  # Optional: build category metadata
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

    all_rows: list[list[str | int | float]] = []
    global_column_boundaries = config.get("column_boundaries")
    merge_continuation = config.get("merge_continuation_rows", False)
    num_columns = len(headers)

    # Process each region (sub-table)
    for region in regions:
        # Each region can optionally specify a page, otherwise use pages[0]
        region_page = region.get("page", pages[0])
        page_obj = doc[region_page - 1]
        words = page_obj.get_text("words")

        x_min = region.get("x_min", 0)
        x_max = region.get("x_max", 999999)
        y_min = region.get("y_min", 0)
        y_max = region.get("y_max", 999999)

        # Filter words to region
        region_words = [w for w in words if x_min <= w[0] < x_max and y_min <= w[1] <= y_max]

        # Group by Y-coordinate
        rows_dict = group_words_by_y(region_words)

        region_rows: list[list[str | int | float]] = []

        # Check for per-region boundaries, fall back to global
        column_boundaries = region.get("column_boundaries", global_column_boundaries)

        # If column_boundaries specified, use coordinate-based column splitting
        if column_boundaries:
            for _y_pos, row_words in sorted(rows_dict.items()):
                sorted_words = sorted(row_words, key=lambda w: w[0])

                row = []
                for col_idx in range(num_columns):
                    # Determine column x-range (boundaries are relative to region x_min)
                    x_start = x_min + column_boundaries[col_idx - 1] if col_idx > 0 else x_min
                    x_end = (
                        x_min + column_boundaries[col_idx]
                        if col_idx < len(column_boundaries)
                        else x_max
                    )

                    # Collect words in this column
                    col_words = [text for x, text in sorted_words if x_start <= x < x_end]
                    row.append(" ".join(col_words))

                # Skip header rows (check for actual header row, not just matching values)
                # For class progressions, "1st"/"2nd" etc appear both in Level column AND as spell slot headers
                # Only skip if multiple cells match headers exactly (indicating the header row itself)
                if row:
                    matching_headers = sum(
                        1 for cell in row if any(h.lower() == cell.lower().strip() for h in headers)
                    )
                    non_empty = sum(1 for cell in row if cell.strip())
                    # Skip if more than half the cells are exact header matches
                    if non_empty > 0 and matching_headers > non_empty / 2:
                        continue

                    region_rows.append(row)  # type: ignore[arg-type]

            # Merge continuation rows if requested
            if merge_continuation and region_rows:
                merged_rows: list[list[str | int | float]] = []
                for row in region_rows:  # type: ignore[assignment]
                    if merged_rows and not str(row[0]).strip():
                        # Empty first column: merge with previous row
                        for col_idx in range(len(row)):
                            if str(row[col_idx]).strip():
                                prev_val = merged_rows[-1][col_idx]
                                merged_rows[-1][col_idx] = str(prev_val) + " " + str(row[col_idx])
                    else:
                        # Non-empty first column: new row
                        merged_rows.append(row)  # type: ignore[arg-type]
                region_rows = merged_rows

            all_rows.extend(region_rows)

        else:
            # Legacy text parsing (join all words, split, parse)
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

    # Filter empty first column rows if requested (for class progressions)
    filter_empty_first = config.get("filter_empty_first_column", False)
    if filter_empty_first and all_rows:
        all_rows = [row for row in all_rows if str(row[0]).strip()]

    doc.close()

    # Build category metadata if requested
    metadata = None
    detect_categories = config.get("detect_categories", False)
    if detect_categories and all_rows:
        metadata = _build_category_metadata(all_rows, headers)

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
        metadata=metadata,
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

    Uses coordinate-based extraction with get_text("words") - same proven approach
    as split_column pattern. Extracts words from region and groups by Y-coordinate.

    Config requirements:
        - pages: [int] - Single page number
        - headers: list[str] - Column headers
        - region: dict with x_min, x_max, y_min, y_max coordinates
    """
    import pymupdf

    from .text_parser_utils import group_words_by_y

    pages = config["pages"]
    if not isinstance(pages, list) or len(pages) != 1:
        raise ValueError(f"{simple_name}: text_region requires single page, got {pages}")

    page_num = pages[0]
    headers = config["headers"]
    region = config["region"]
    num_columns = len(headers)

    doc = pymupdf.open(pdf_path)
    page_obj = doc[page_num - 1]  # Convert to 0-indexed

    # Get all words from page
    words = page_obj.get_text("words")
    doc.close()

    # Filter words to region and group by Y-coordinate
    rows_dict = group_words_by_y(
        words,
        y_tolerance=2.0,
        x_min=region["x_min"],
        x_max=region["x_max"],
        y_min=region["y_min"],
        y_max=region["y_max"],
    )

    # Build table rows
    rows: list[list[str | int | float]] = []

    # Check if column boundaries are specified
    column_boundaries = config.get("column_boundaries")

    if column_boundaries:
        # Multi-column with explicit boundaries: group words into columns by x-coordinate
        # column_boundaries = [x1, x2, x3] means: col1: [min, x1), col2: [x1, x2), col3: [x2, x3), col4: [x3, max)
        for _y_pos, row_words in sorted(rows_dict.items()):
            sorted_words = sorted(row_words, key=lambda w: w[0])

            row = []
            for col_idx in range(num_columns):
                # Determine column x-range
                x_start = column_boundaries[col_idx - 1] if col_idx > 0 else region["x_min"]
                x_end = (
                    column_boundaries[col_idx]
                    if col_idx < len(column_boundaries)
                    else region["x_max"]
                )

                # Collect words in this column
                col_words = [text for x, text in sorted_words if x_start <= x < x_end]
                row.append(" ".join(col_words))

            # Skip header rows (check for actual header row, not just matching values)
            if row:
                matching_headers = sum(
                    1
                    for cell in row
                    if any(h.lower() == str(cell).lower().strip() for h in headers)
                )
                non_empty = sum(1 for cell in row if str(cell).strip())
                # Skip if more than half the cells are exact header matches
                if non_empty > 0 and matching_headers > non_empty / 2:
                    continue

                rows.append(row)  # type: ignore[arg-type]

        # Post-process: merge continuation rows (rows where first column is empty)
        # These are typically units or additional info on subsequent lines
        merged_rows: list[list[str | int | float]] = []
        for row in rows:  # type: ignore[assignment]
            if merged_rows and not row[0]:
                # Empty first column: merge with previous row
                for col_idx in range(len(row)):
                    if row[col_idx]:
                        prev_val = merged_rows[-1][col_idx]
                        merged_rows[-1][col_idx] = str(prev_val) + " " + str(row[col_idx])
            else:
                # Non-empty first column: new row
                merged_rows.append(row)  # type: ignore[arg-type]
        rows = merged_rows

    elif num_columns == 2:
        # Two-column table: use column_split_x if provided, otherwise midpoint
        split_x = config.get("column_split_x", (region["x_min"] + region["x_max"]) / 2)
        for _y_pos, row_words in sorted(rows_dict.items()):
            sorted_words = sorted(row_words, key=lambda w: w[0])
            col1 = " ".join([text for x, text in sorted_words if x < split_x])
            col2 = " ".join([text for x, text in sorted_words if x >= split_x])

            if col1 and col2:
                rows.append([col1, col2])
    else:
        # Multi-column without boundaries: concatenate all words as single row
        for _y_pos, row_words in sorted(rows_dict.items()):
            sorted_words = sorted(row_words, key=lambda w: w[0])
            row_text = " ".join([text for _, text in sorted_words])
            if row_text:
                rows.append([row_text])

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

    Used for tables that span multiple pages with different regions per page.

    Config requirements:
        - pages: list[int] - Page numbers
        - headers: list[str] - Column headers
        - regions: list[dict] - One region per page, each with:
            - page: int - Page number
            - x_min, x_max, y_min, y_max: coordinates
    """
    import pymupdf

    from .text_parser_utils import group_words_by_y

    pages = config["pages"]
    headers = config["headers"]
    regions = config["regions"]
    num_columns = len(headers)

    # Validate regions
    if len(regions) != len(pages):
        raise ValueError(
            f"{simple_name}: multipage_text_region requires one region per page, "
            f"got {len(regions)} regions for {len(pages)} pages"
        )

    doc = pymupdf.open(pdf_path)

    # Collect all rows from all pages
    all_rows_dict = {}

    for region in regions:
        page_num = region["page"]
        page_obj = doc[page_num - 1]  # Convert to 0-indexed

        # Get all words from page
        words = page_obj.get_text("words")

        # Filter words to region and group by Y-coordinate
        rows_dict = group_words_by_y(
            words,
            y_tolerance=2.0,
            x_min=region["x_min"],
            x_max=region["x_max"],
            y_min=region["y_min"],
            y_max=region["y_max"],
        )

        # Merge with global offset to maintain sort order across pages
        # Use page_num * 1000 + y_pos to ensure proper ordering
        for y_pos, row_words in rows_dict.items():
            global_y = page_num * 1000 + y_pos
            all_rows_dict[global_y] = row_words

    doc.close()

    # Build table rows
    rows: list[list[str | int | float]] = []
    column_boundaries = config.get("column_boundaries")

    if column_boundaries:
        # Multi-column with explicit boundaries
        for _y_pos, row_words in sorted(all_rows_dict.items()):
            sorted_words = sorted(row_words, key=lambda w: w[0])

            row = []
            for col_idx in range(num_columns):
                # Use first region for column boundary reference
                x_start = column_boundaries[col_idx - 1] if col_idx > 0 else regions[0]["x_min"]
                x_end = (
                    column_boundaries[col_idx]
                    if col_idx < len(column_boundaries)
                    else regions[0]["x_max"]
                )

                col_words = [text for x, text in sorted_words if x_start <= x < x_end]
                row.append(" ".join(col_words))

            if row:
                rows.append(row)  # type: ignore[arg-type]
    else:
        # Single-column or simple layout
        for _y_pos, row_words in sorted(all_rows_dict.items()):
            sorted_words = sorted(row_words, key=lambda w: w[0])
            row_text = " ".join([text for _, text in sorted_words])
            if row_text.strip():
                rows.append([row_text])

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=headers,
        rows=rows,
        extraction_method="multipage_text_region",
        section=section,
        notes=config.get("notes", ""),
        chapter=config.get("chapter"),
        confirmed=config.get("confirmed", False),
        source=config.get("source", "srd"),
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


def _extract_prose_section(
    table_id: str,
    simple_name: str,
    page: int | list[int],
    config: dict[str, Any],
    section: str | None,
    pdf_path: str,
) -> RawTable:
    """Extract prose sections (conditions, diseases, equipment descriptions, etc.).

    Config fields:
        - known_headers: list[str] - Known section names (empty = dynamic discovery)
        - pages: tuple[int, int] - (start_page, end_page)

    Returns prose sections as a "table" with:
        headers: ["name", "text", "page"]
        rows: [[section_name, prose_text, page_num], ...]
    """
    from pathlib import Path

    from ..utils.prose import ProseExtractor

    # Get page range
    if isinstance(page, list):
        start_page, end_page = page[0], page[-1]
    else:
        start_page = end_page = page

    # Override with config pages if provided
    if "pages" in config:
        start_page, end_page = config["pages"]

    # Extract using ProseExtractor
    extractor = ProseExtractor(
        section_name=config.get("entity_type", simple_name),
        known_headers=config.get("known_headers", []),
        start_page=start_page,
        end_page=end_page,
    )

    sections, warnings = extractor.extract_from_pdf(Path(pdf_path))

    # Convert to table format
    rows = []
    for sect in sections:
        rows.append([sect["name"], sect["raw_text"], sect["page"]])

    if warnings:
        logger.warning(f"Prose extraction warnings for {simple_name}: {warnings}")

    return RawTable(
        table_id=table_id,
        simple_name=simple_name,
        page=page,
        headers=["name", "text", "page"],
        rows=rows,
        extraction_method="prose_section",
        section=section,
        notes=config.get("notes"),
        chapter=config.get("chapter"),
        confirmed=config.get("confirmed", False),
        source="srd",
    )


# ═══════════════════════════════════════════════════════════════════════════
# RECORD-SHAPED ENGINES (called via extract_records_by_config)
# ═══════════════════════════════════════════════════════════════════════════

# Default structural-text filter patterns (page footers, page numbers, common
# in-class table titles). Extractors can override via config["structural_patterns"].
_DEFAULT_STRUCTURAL_PATTERNS = (
    r"^System Reference Document",
    r"^\d+$",
    r"^The [A-Z][a-z]+ Table",
    r"^Level\s+Proficiency",
    r"^Spell Slots per Spell Level",
)

# PyMuPDF span flag bits.
_SPAN_FLAG_ITALIC = 2**1
_SPAN_FLAG_BOLD = 2**4


def _span_matches_fingerprint(span: dict[str, Any], fp: dict[str, Any]) -> bool:
    """Test a single span against a header fingerprint config."""
    text = span["text"].strip()
    if len(text) < fp.get("min_text_len", 1):
        return False
    if fp.get("require_trailing_period", False) and not text.endswith("."):
        return False

    size = span.get("size", 0)
    if not (fp["size_min"] <= size <= fp["size_max"]):
        return False

    font = span.get("font", "")
    if fp["font_substring"] not in font:
        return False

    flags = span.get("flags", 0)
    if fp.get("require_bold", False) and not (flags & _SPAN_FLAG_BOLD):
        return False
    if fp.get("require_italic", False) and not (flags & _SPAN_FLAG_ITALIC):
        return False

    return True


def _resolve_body_cleanup(name: str | None) -> Any:
    """Resolve a body_cleanup config name to a callable. None → identity."""
    if name is None:
        return lambda s: s
    if name == "clean_text":
        from ..utils.prose import clean_text

        return clean_text
    raise ValueError(f"Unknown body_cleanup '{name}'")


def _simplify_span(span: dict[str, Any]) -> dict[str, Any]:
    """Convert a PyMuPDF span dict into the simplified per-bucket form used by
    font_split_spans body_grouping. Shape: {text, font, size, is_bold, is_italic}.
    """
    font = span.get("font", "")
    return {
        "text": span.get("text", ""),
        "font": font,
        "size": round(span.get("size", 0), 1),
        "is_bold": "Bold" in font or "SemiBold" in font,
        "is_italic": "Italic" in font,
    }


def _line_bucket_for_spans(
    line_spans: list[dict[str, Any]], body_buckets: list[dict[str, Any]]
) -> str:
    """For font_split_spans: decide which bucket a line's spans belong in.

    A bucket may declare match_any_span={font_substring, require_italic, require_bold}.
    The first bucket whose predicate matches any span in the line wins.
    A bucket marked {"default": True} is the fallback.
    """
    default_name: str | None = None
    for bucket in body_buckets:
        if bucket.get("default", False):
            default_name = bucket["name"]
            continue
        predicate = bucket.get("match_any_span", {})
        font_sub = predicate.get("font_substring", "")
        need_italic = predicate.get("require_italic", False)
        need_bold = predicate.get("require_bold", False)
        for span in line_spans:
            font = span.get("font", "")
            if font_sub and font_sub not in font:
                continue
            if need_italic and not span.get("is_italic", False):
                continue
            if need_bold and not span.get("is_bold", False):
                continue
            return bucket["name"]
    if default_name is None:
        raise ValueError("font_split_spans body_buckets must include one {'default': True}")
    return default_name


def _post_pass_merge_short_records(
    records: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    """Merge records whose check-bucket text is below threshold AND whose
    skip-bucket is empty, by prepending their spans into the next record.

    Mirrors the cross-page heuristic in extract_magic_items._merge_multipage_items.
    """
    if not records:
        return []
    threshold = config["merge_threshold"]
    check_bucket = config["merge_check_bucket"]
    skip_bucket = config.get("merge_skip_if_bucket_nonempty")

    merged: list[dict[str, Any]] = []
    current = records[0]
    for nxt in records[1:]:
        check_text_len = sum(len(s.get("text", "")) for s in current.get(check_bucket, []))
        skip = skip_bucket is not None and len(current.get(skip_bucket, [])) > 0
        if check_text_len < threshold and not skip:
            nxt[check_bucket] = current.get(check_bucket, []) + nxt.get(check_bucket, [])
        else:
            merged.append(current)
        current = nxt
    merged.append(current)
    return merged


def _extract_font_fingerprint_walk(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Walk pages and detect record headers by font fingerprint.

    Config schema (defaults in brackets):
        {
            "pattern_type": "font_fingerprint_walk",
            "header_fingerprints": [
                {
                    "font_substring": "GillSans",
                    "size_min": 13.5,
                    "size_max": 14.5,
                    "require_bold": True,
                    "require_italic": False,                  # optional
                    "min_text_len": 2,
                    "require_trailing_period": False,         # optional
                    "strip_trailing_period_from_name": False, # optional
                },
                # ...additional fingerprints OR'd together
            ],
            "header_scope": "span" | "line",                  # ["span"]
            "header_match_mode": "any_span" | "first_span",   # ["any_span"]; line-mode only
            "header_continuation_words": ["and", "or", ...],  # [None]; line-mode only
            "body_grouping": "single_bucket_concat" | "font_split_spans",
                                                              # ["single_bucket_concat"]
            "body_cleanup": "clean_text" | None,              # [None]; concat mode only
            "body_buckets": [                                 # font_split_spans only
                {"name": "metadata_blocks",
                 "match_any_span": {"font_substring": "Cambria",
                                    "require_italic": True}},
                {"name": "description_blocks", "default": True},
            ],
            "filter_structural": True,                        # [False]
            "structural_patterns": [...],                     # [_DEFAULT]
            "page_reset_record": True,                        # [True]
            "post_pass": "merge_short_records" | None,        # [None]
            "merge_threshold": 20,                            # post-pass param
            "merge_check_bucket": "description_blocks",
            "merge_skip_if_bucket_nonempty": "metadata_blocks",
        }

    Returns:
        list[dict] — one record per detected header. Shape depends on
        body_grouping:
            single_bucket_concat → {"name", "text", "page"}
            font_split_spans     → {"name", "page", <bucket_name>: [span_dicts]}
    """
    fingerprints = config["header_fingerprints"]
    if not fingerprints:
        raise ValueError("font_fingerprint_walk requires at least one header_fingerprints entry")

    header_scope = config.get("header_scope", "span")
    if header_scope == "span":
        return _font_fingerprint_walk_span_mode(pdf_path, pages, config)
    if header_scope == "line":
        return _font_fingerprint_walk_line_mode(pdf_path, pages, config)
    raise ValueError(f"Unknown header_scope '{header_scope}' (known: span, line)")


def _font_fingerprint_walk_span_mode(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Span-level header detection; single_bucket_concat body grouping only.

    Original prototype path used by extract_features. Kept narrow on purpose:
    new pattern complexity goes in _font_fingerprint_walk_line_mode().
    """
    from pathlib import Path

    from ..utils.pdf_probe import open_pdf

    fingerprints = config["header_fingerprints"]
    filter_structural = config.get("filter_structural", False)
    structural_re_list = [
        re.compile(p) for p in (config.get("structural_patterns") or _DEFAULT_STRUCTURAL_PATTERNS)
    ]
    body_cleanup = _resolve_body_cleanup(config.get("body_cleanup"))
    page_reset_record = config.get("page_reset_record", True)

    def _is_structural(text: str) -> bool:
        return any(rx.match(text) for rx in structural_re_list)

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    with open_pdf(Path(pdf_path)) as pdf:
        for page_num in pages:
            if page_reset_record and current is not None:
                records.append(current)
                current = None

            page = pdf[page_num - 1]
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        matched_fp: dict[str, Any] | None = None
                        for fp in fingerprints:
                            if _span_matches_fingerprint(span, fp):
                                matched_fp = fp
                                break

                        if matched_fp is not None:
                            if current is not None:
                                records.append(current)
                            name = text
                            if matched_fp.get("strip_trailing_period_from_name", False):
                                name = name.rstrip(".")
                            current = {"name": name, "text": "", "page": page_num}
                        elif current is not None and text:
                            if filter_structural and _is_structural(text):
                                continue
                            current["text"] += text + " "

    if current is not None:
        records.append(current)

    for r in records:
        r["text"] = body_cleanup(r["text"].strip())

    return records


def _font_fingerprint_walk_line_mode(
    pdf_path: str,
    pages: list[int],
    config: dict[str, Any],
) -> list[dict[str, Any]]:
    """Line-level header detection with continuation, font-split body grouping,
    and optional cross-record post-pass merge.

    Used by extract_magic_items. Mirrors the original bespoke logic:
        - Header detected by checking the FIRST span of each line (mode
          'first_span') or ANY span ('any_span') against fingerprints.
        - If a header line ends in one of header_continuation_words, the next
          header line's text is appended and only the merged name is committed
          on the next non-header line.
        - body_grouping 'font_split_spans': line-level spans collected as
          simplified dicts and routed to a bucket based on per-line predicate.
        - Optional post_pass merges short records into the next.
    """
    from pathlib import Path

    from ..utils.pdf_probe import open_pdf

    fingerprints = config["header_fingerprints"]
    match_mode = config.get("header_match_mode", "any_span")
    continuation_words: set[str] = {
        w.lower() for w in (config.get("header_continuation_words") or [])
    }
    body_grouping = config.get("body_grouping", "single_bucket_concat")
    page_reset_record = config.get("page_reset_record", True)

    if body_grouping != "font_split_spans":
        raise ValueError(
            f"line header_scope currently requires body_grouping='font_split_spans' "
            f"(got '{body_grouping}')"
        )
    body_buckets = config["body_buckets"]
    bucket_names = [b["name"] for b in body_buckets]

    def _new_record(name: str, page_num: int) -> dict[str, Any]:
        rec: dict[str, Any] = {"name": name, "page": page_num}
        for b in bucket_names:
            rec[b] = []
        return rec

    def _line_matches_header(line_spans_raw: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not line_spans_raw:
            return None
        candidates = [line_spans_raw[0]] if match_mode == "first_span" else line_spans_raw
        for span in candidates:
            for fp in fingerprints:
                if _span_matches_fingerprint(span, fp):
                    return fp
        return None

    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    pending_name: str | None = None
    pending_fp: dict[str, Any] | None = None

    with open_pdf(Path(pdf_path)) as pdf:
        for page_num in pages:
            page = pdf[page_num - 1]
            for block in page.get_text("dict")["blocks"]:
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    raw_spans = line.get("spans", [])
                    if not raw_spans:
                        continue
                    simple_spans = [_simplify_span(s) for s in raw_spans]
                    line_text = "".join(s["text"] for s in simple_spans).strip()
                    if not line_text:
                        continue

                    header_fp = _line_matches_header(raw_spans)

                    if header_fp is not None:
                        # Header line. Build / extend the pending name.
                        if pending_name is not None:
                            pending_name = pending_name.strip() + " " + line_text
                        else:
                            pending_name = line_text
                            pending_fp = header_fp
                        # Defer commit if trailing word signals continuation.
                        last_word = pending_name.split()[-1].lower() if pending_name.split() else ""
                        if last_word in continuation_words:
                            continue
                        # Otherwise fall through: header is complete on this line,
                        # but the original code only finalizes on the *next*
                        # non-header line. Preserve that timing.
                        continue

                    # Non-header line. If we have a pending header, finalize it
                    # into a new record now.
                    if pending_name is not None:
                        if current is not None:
                            records.append(current)
                        name = pending_name
                        if pending_fp is not None and pending_fp.get(
                            "strip_trailing_period_from_name", False
                        ):
                            name = name.rstrip(".")
                        current = _new_record(name, page_num)
                        pending_name = None
                        pending_fp = None

                    if current is None:
                        continue
                    bucket = _line_bucket_for_spans(simple_spans, body_buckets)
                    current[bucket].extend(simple_spans)

            # End of page. Flush any pending name as its own record (mirrors
            # the original per-page finalize behavior).
            if pending_name is not None:
                if current is not None:
                    records.append(current)
                name = pending_name
                if pending_fp is not None and pending_fp.get(
                    "strip_trailing_period_from_name", False
                ):
                    name = name.rstrip(".")
                current = _new_record(name, page_num)
                pending_name = None
                pending_fp = None

            if page_reset_record and current is not None:
                records.append(current)
                current = None

    if current is not None:
        records.append(current)

    post_pass = config.get("post_pass")
    if post_pass == "merge_short_records":
        records = _post_pass_merge_short_records(records, config)
    elif post_pass is not None:
        raise ValueError(f"Unknown post_pass '{post_pass}'")

    return records
