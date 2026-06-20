"""Multipage text region pattern: text extracted across multiple page bboxes."""

from __future__ import annotations

import logging
from typing import Any

from ._types import RawTable

logger = logging.getLogger(__name__)


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

    from ..text_parser_utils import group_words_by_y

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
