"""Public dataclasses for the patterns package."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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
