"""Prose section pattern: named prose sections."""

from __future__ import annotations

import logging
from typing import Any

from ._types import RawTable

logger = logging.getLogger(__name__)


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

    from ...utils.prose import ProseExtractor

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
