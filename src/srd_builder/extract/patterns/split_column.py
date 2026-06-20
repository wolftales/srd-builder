"""Split-column pattern: side-by-side sub-tables in one page region."""

from __future__ import annotations

import logging
from typing import Any

from ._types import RawTable
from .calculated import _build_category_metadata
from .standard_grid import _parse_row

logger = logging.getLogger(__name__)


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

    from ..text_parser_utils import group_words_by_y

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
