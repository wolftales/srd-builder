"""Standard grid pattern: PyMuPDF auto-detected grid tables."""

from __future__ import annotations

import logging
from typing import Any

from ._types import RawTable

logger = logging.getLogger(__name__)


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
