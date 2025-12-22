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

    from ..extract.extract_prose import ProseExtractor

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
