"""Identifier helpers shared across postprocessing steps."""

from __future__ import annotations

import re

__all__ = ["normalize_id"]

# Normalized IDs are restricted to lowercase letters, digits, and underscores.
_ID_CLEAN_RE = re.compile(r"[^0-9a-z_]+")


def normalize_id(value: str) -> str:
    """Normalize arbitrary text into a lowercase underscore identifier."""

    simplified = value.strip().lower()
    simplified = simplified.replace("-", "_").replace(" ", "_")
    simplified = _ID_CLEAN_RE.sub("", simplified)
    simplified = re.sub(r"_+", "_", simplified)
    return simplified.strip("_")
