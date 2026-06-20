"""Reference pattern: static hardcoded data (fallback)."""

from __future__ import annotations

import logging
from typing import Any

from ._types import RawTable

logger = logging.getLogger(__name__)


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
