"""Utility functions for text-based table parsing.

Common operations extracted from text_table_parser.py to reduce duplication
and provide reusable building blocks for coordinate-based PDF text extraction.
"""

from typing import Any

import fitz


def group_words_by_y(
    words: list[tuple[Any, ...]],
    y_tolerance: float = 2.0,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
) -> dict[float, list[tuple[float, str]]]:
    """Group PDF words by Y-coordinate (horizontal rows).

    Args:
        words: List of word tuples from page.get_text("words")
        y_tolerance: Pixels within which words are considered on same row
        x_min: Optional minimum X-coordinate filter
        x_max: Optional maximum X-coordinate filter
        y_min: Optional minimum Y-coordinate filter
        y_max: Optional maximum Y-coordinate filter

    Returns:
        Dictionary mapping Y-coordinate to list of (X, text) tuples
    """
    rows: dict[float, list[tuple[float, str]]] = {}

    for word in words:
        x0, y0, x1, y1, text, *_ = word

        # Apply coordinate filters
        if x_min is not None and x0 < x_min:
            continue
        if x_max is not None and x0 >= x_max:
            continue
        if y_min is not None and y0 < y_min:
            continue
        if y_max is not None and y0 >= y_max:
            continue

        # Group by rounded Y-coordinate
        y_key = round(y0 / y_tolerance) * y_tolerance
        if y_key not in rows:
            rows[y_key] = []
        rows[y_key].append((x0, text))

    return rows


def extract_region_rows(
    pdf_path: str,
    page_num: int,
    x_min: float | None = None,
    x_max: float | None = None,
    y_min: float | None = None,
    y_max: float | None = None,
    y_tolerance: float = 2.0,
) -> dict[float, list[tuple[float, str]]]:
    """Extract rows from a specific PDF page region.

    Args:
        pdf_path: Path to PDF file
        page_num: Page number (1-indexed)
        x_min: Optional minimum X-coordinate
        x_max: Optional maximum X-coordinate
        y_min: Optional minimum Y-coordinate
        y_max: Optional maximum Y-coordinate
        y_tolerance: Y-coordinate grouping tolerance

    Returns:
        Dictionary mapping Y-coordinate to list of (X, text) tuples
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    words = page.get_text("words")
    doc.close()

    return group_words_by_y(words, y_tolerance, x_min, x_max, y_min, y_max)


def find_currency_index(words: list[str]) -> int | None:
    """Find index of currency word (gp, sp, cp) in word list.

    Args:
        words: List of words to search

    Returns:
        Index of currency word, or None if not found
    """
    for i, word in enumerate(words):
        if word in ["gp", "sp", "cp"]:
            return i
    return None


def split_at_currency(words: list[str], currency_idx: int) -> tuple[list[str], str, list[str]]:
    """Split word list at currency position.

    Typical pattern: name words... | amount currency | remaining words...

    Args:
        words: List of words
        currency_idx: Index of currency word (gp/sp/cp)

    Returns:
        Tuple of (name_parts, cost_with_currency, remaining_parts)
    """
    # Name: everything before cost amount
    name_parts = words[: currency_idx - 1]

    # Cost: amount + currency
    cost = f"{words[currency_idx - 1]} {words[currency_idx]}"

    # Remaining: everything after currency
    remaining_parts = words[currency_idx + 1 :]

    return name_parts, cost, remaining_parts


def merge_multipage_rows(
    rows_page1: dict[float, list[tuple[float, str]]],
    rows_page2: dict[float, list[tuple[float, str]]],
) -> dict[float, list[tuple[float, str]]]:
    """Merge row dictionaries from multiple pages.

    Preserves Y-coordinates from both pages for proper ordering.

    Args:
        rows_page1: Row dictionary from first page
        rows_page2: Row dictionary from second page

    Returns:
        Combined row dictionary with all rows
    """
    return {**rows_page1, **rows_page2}


def rows_to_sorted_text(
    rows: dict[float, list[tuple[float, str]]],
) -> list[tuple[float, list[str]]]:
    """Convert row dictionary to sorted list with text only.

    Args:
        rows: Dictionary mapping Y-coordinate to list of (X, text) tuples

    Returns:
        List of (Y-coordinate, sorted_words) tuples, ordered by Y (top to bottom)
    """
    result = []
    for y_pos in sorted(rows.keys()):
        # Sort words by X-coordinate (left to right)
        row_words = sorted(rows[y_pos], key=lambda w: w[0])
        words_list = [text for x, text in row_words]
        result.append((y_pos, words_list))
    return result


def should_skip_header(row_text: str, header_patterns: list[str]) -> bool:
    """Check if row should be skipped as a header.

    Args:
        row_text: Joined text of row
        header_patterns: List of patterns that indicate headers

    Returns:
        True if row matches any header pattern
    """
    return any(pattern in row_text for pattern in header_patterns)


def detect_indentation(row_words: list[tuple[float, str]], threshold: float) -> bool:
    """Check if row is indented based on first word X-coordinate.

    Args:
        row_words: List of (X, text) tuples for row
        threshold: X-coordinate above which row is considered indented

    Returns:
        True if row is indented
    """
    if not row_words:
        return False
    first_x = row_words[0][0]
    return first_x > threshold
