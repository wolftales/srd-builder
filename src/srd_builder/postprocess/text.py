"""Text cleanup helpers shared across postprocessing modules."""

from __future__ import annotations

import re
from typing import Any

__all__ = ["clean_text", "polish_text", "polish_text_fields"]

_LEGENDARY_SENTENCES = [
    re.compile(r"The [^.]+ can take [^.]+ legendary actions[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"Only one legendary action option can be used at a time\.\s*", re.IGNORECASE),
    re.compile(r"The [^.]+ regains spent legendary actions[^.]*\.\s*", re.IGNORECASE),
]


def clean_text(text: str) -> str:
    """Clean up common text encoding issues.

    Consolidates text cleaning used across extraction and postprocessing.
    Fixes encoding artifacts, normalizes whitespace, and handles special characters.

    CRITICAL: Removes control characters (\\t, \\r, etc.) that corrupt text extraction.
    These characters appear in spell descriptions, monster traits, and other text blocks
    from data sources (PDF, etc.) and must be stripped before any processing.

    Args:
        text: Raw text from data source

    Returns:
        Cleaned text with normalized whitespace and fixed encoding
    """
    # FIRST: Remove control characters that corrupt extraction (\t\r\n\xa0, etc.)
    # This must happen before other replacements to prevent corruption
    text = re.sub(r"[\t\r\n\u00ad\u2010\u2011\u00a0]+", " ", text)

    # Fix common PDF encoding issues
    text = text.replace("­‐‑", "-")  # Replace garbled dashes (soft hyphen + hyphens)
    text = text.replace("­‐", "-")
    text = text.replace("‑", "-")
    text = text.replace("–", "-")  # en-dash
    text = text.replace("—", "--")  # em-dash
    text = text.replace("'", "'")  # smart quotes
    text = text.replace(
        """, '"')
    text = text.replace(""",
        '"',
    )

    # Normalize all whitespace sequences to single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def polish_text(text: str | None) -> str | None:
    """Clean OCR artifacts, spacing, and boilerplate from text fields."""

    if text is None:
        return None

    cleaned = text
    for pattern in _LEGENDARY_SENTENCES:
        cleaned = pattern.sub("", cleaned)

    cleaned = cleaned.replace("\u2013", "—").replace("\u2014", "—")
    cleaned = re.sub(r"--+", "—", cleaned)
    cleaned = re.sub(r"\bH\s*it\b", "Hit", cleaned)
    cleaned = re.sub(r"Hit:\s*(\d)", r"Hit: \1", cleaned)
    cleaned = re.sub(r"(\d+d\d+)\s*([+-])\s*(\d+)", r"\1 \2 \3", cleaned)
    cleaned = cleaned.replace("keepsgoing", "keeps going")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"([.!?])([A-Z])", r"\1 \2", cleaned)
    cleaned = cleaned.strip()
    return cleaned


def polish_text_fields(monster: dict[str, Any]) -> dict[str, Any]:
    """Apply :func:`polish_text` to summary, traits, actions, and legendary actions."""

    patched = {**monster}

    if "summary" in patched and isinstance(patched["summary"], str):
        patched["summary"] = polish_text(patched["summary"]) or ""

    for key in ("traits", "actions", "legendary_actions", "reactions"):
        if key not in monster:
            continue
        formatted: list[dict[str, Any]] = []
        for entry in monster.get(key, []):
            if not isinstance(entry, dict):
                formatted.append(entry)
                continue
            item = {**entry}

            # Polish description paragraphs
            if "description" in item and isinstance(item["description"], list):
                polished_paras = []
                for para in item["description"]:
                    if isinstance(para, str):
                        polished = polish_text(para)
                        if polished is not None:
                            polished_paras.append(polished)
                if polished_paras:
                    item["description"] = polished_paras

            if "name" in item and isinstance(item["name"], str):
                item["name"] = item["name"].rstrip(".")
            formatted.append(item)
        patched[key] = formatted

    return patched
