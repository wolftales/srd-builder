"""extract_by_config / extract_records_by_config routing."""

from __future__ import annotations

from typing import Any

from ._types import RawTable
from .calculated import _extract_calculated
from .font_fingerprint_walk import _extract_font_fingerprint_walk
from .font_stateful_walk import _extract_font_stateful_walk
from .multipage_text_region import _extract_multipage_text_region
from .prose_section import _extract_prose_section
from .reference import _extract_reference
from .split_column import _extract_split_column
from .standard_grid import _extract_standard_grid
from .text_region import _extract_text_region


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
    - font_stateful_walk    → _extract_font_stateful_walk()
    """
    pattern_type = config.get("pattern_type")
    if not pattern_type:
        raise ValueError("Record-shaped config missing required 'pattern_type' field")

    if pattern_type == "font_fingerprint_walk":
        return _extract_font_fingerprint_walk(pdf_path, pages, config)
    if pattern_type == "font_stateful_walk":
        return _extract_font_stateful_walk(pdf_path, pages, config)

    raise ValueError(
        f"Unknown record-shaped pattern_type '{pattern_type}' "
        f"(known: font_fingerprint_walk, font_stateful_walk)"
    )
