"""Text region pattern: text extracted from a single page bbox."""

from __future__ import annotations

import logging
from typing import Any

from ._types import RawTable

logger = logging.getLogger(__name__)


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

    from ..text_parser_utils import group_words_by_y

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
