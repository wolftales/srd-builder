"""Text cleanup helpers shared across postprocessing modules."""

from __future__ import annotations

import re
from typing import Any

__all__ = ["clean_pdf_text", "polish_text", "polish_text_fields"]

_LEGENDARY_SENTENCES = [
    re.compile(r"The [^.]+ can take [^.]+ legendary actions[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"Only one legendary action option can be used at a time\.\s*", re.IGNORECASE),
    re.compile(r"The [^.]+ regains spent legendary actions[^.]*\.\s*", re.IGNORECASE),
]


def clean_pdf_text(text: str) -> str:
    """Clean up common PDF encoding issues.

    Consolidates text cleaning used across extraction and postprocessing.
    Fixes encoding artifacts, normalizes whitespace, and handles special characters.

    Args:
        text: Raw text from PDF

    Returns:
        Cleaned text with normalized whitespace and fixed encoding
    """
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
    text = text.replace("\n", " ")  # Normalize newlines to spaces
    text = re.sub(r"\s+", " ", text)  # Collapse multiple whitespace
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
            if "text" in item:
                polished = polish_text(item["text"])
                if polished is not None:
                    item["text"] = polished
            if "name" in item and isinstance(item["name"], str):
                item["name"] = item["name"].rstrip(".")
            formatted.append(item)
        patched[key] = formatted

    return patched
