"""PyMuPDF table-extraction primitives.

These helpers operate on the row-of-cells output produced by
``fitz.Page.find_tables().tables[i].extract()`` — a ``list[list[str |
None]]`` where each cell may be ``None`` for empty positions. They
provide the small, repeatable transforms that every PDF table extractor
needs (cell normalization, header detection) while leaving the
dataset-specific column semantics to the caller.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence


def clean_and_split_header(
    table_rows: Sequence[Sequence[str | None]] | None,
    *,
    header_predicate: Callable[[list[str]], bool],
) -> tuple[list[str] | None, list[list[str]]]:
    """Normalize ``table_rows`` and detect whether the first data row is
    a header.

    Each cell is coerced to a stripped string (``None`` becomes ``""``).
    Rows where every cell is empty are dropped. The first surviving row
    is passed to ``header_predicate``; if the predicate returns ``True``
    the row is returned as the header and the rest are returned as data
    rows, otherwise the header is ``None`` and all rows are data.

    Returns ``(header_or_None, data_rows)``. Empty / all-empty input
    yields ``(None, [])``.
    """
    if not table_rows:
        return None, []

    cleaned_rows: list[list[str]] = []
    for raw_row in table_rows:
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in raw_row]
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return None, []

    header_candidate = cleaned_rows[0]
    if header_predicate(header_candidate):
        return header_candidate, cleaned_rows[1:]

    return None, cleaned_rows
