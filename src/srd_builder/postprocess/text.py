"""Text cleanup helpers shared across postprocessing modules."""

from __future__ import annotations

import re
from typing import Any

__all__ = [
    "clean_text",
    "collapse_soft_hyphen_runs",
    "polish_text",
    "polish_text_fields",
    "strip_srd_page_footer",
]

_SRD_PAGE_FOOTER_RE = re.compile(r"\s*System Reference Document\s+[\d.]+(?:\s+\d+)?\s*")
_SOFT_HYPHEN_RUN_RE = re.compile(r"[-\xad\u2010\u2011]{2,}")


def strip_srd_page_footer(text: str) -> str:
    """Replace the SRD running page footer with a single space.

    The PyMuPDF text stream renders the running ``System Reference
    Document 5.1 67`` footer/header inline with body prose, which
    leaves the marker mid-sentence on cross-page extractions. The
    pattern is version-tolerant (matches ``5.1``, ``5.2.1``, etc.) and
    page-number-optional so callers in postprocess (where text has
    already been concatenated) and in extract (where each page is
    normalized individually) can share one implementation.
    """
    return _SRD_PAGE_FOOTER_RE.sub(" ", text)


def collapse_soft_hyphen_runs(text: str) -> str:
    """Collapse runs of 2+ hyphen-class characters to a single ASCII ``-``.

    PDF line wraps inside hyphenated compounds (``two-handed`` rendered
    across a line break, ``15-foot`` across a column break) leave
    sequences of soft-hyphen (U+00AD), hyphen (U+2010), non-breaking
    hyphen (U+2011), and ASCII ``-`` adjacent in the text stream.
    This helper repairs those runs while preserving singleton hyphens
    so legitimate hyphenated words like ``narrow-bladed`` survive.
    """
    return _SOFT_HYPHEN_RUN_RE.sub("-", text)


_LEGENDARY_SENTENCES = [
    re.compile(r"The [^.]+ can take [^.]+ legendary actions[^.]*\.\s*", re.IGNORECASE),
    re.compile(r"Only one legendary action option can be used at a time\.\s*", re.IGNORECASE),
    re.compile(r"The [^.]+ regains spent legendary actions[^.]*\.\s*", re.IGNORECASE),
]

# PDF line-wrap inside any hyphenated compound: ``two-\nhanded``,
# ``10-\nfoot``, ``Two-\nHeaded``, ``PH-\nA`` all survive whitespace
# normalization as ``leader- follower`` and must be re-joined. Covers
# letter-letter (``two-handed``), digit-letter (``10-foot``),
# letter-digit (``foot-by-5``), letter-Letter (``Two-Headed``,
# ``Sure-Footed``), and letter-single (``PH-A`` appendix refs).
# Suspended-hyphen constructions like ``long- and short-range`` or
# ``5- and 10-foot`` are excluded by refusing follower tokens in the
# coordinating-conjunction set; re.IGNORECASE catches title-case
# variants for defensive depth (the SRD only uses lowercase forms).
# Survey across all 16 datasets in dist showed zero false positives
# for this broader pattern.
_HYPHEN_LINE_BREAK_RE = re.compile(
    r"(\w+)-\s+(?!(?:and|or|but|nor)\b)(\w+)",
    re.IGNORECASE,
)


def _stitch_hyphen_line_breaks(text: str) -> str:
    # Run to fixed point: chained dimensional expressions like
    # ``3- foot- by- 5- foot`` only resolve fully when overlapping
    # matches are re-scanned (``re.sub`` consumes the whole match per
    # substitution and does not rewind).
    while True:
        replaced = _HYPHEN_LINE_BREAK_RE.sub(r"\1-\2", text)
        if replaced == text:
            return text
        text = replaced


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

    # Strip the PDF page footer ("System Reference Document 5.1" + optional
    # page number). Appears mid-prose on cross-page extractions and trailing
    # on single-page ones; both cases collapse to a single space.
    text = strip_srd_page_footer(text)

    # Fix common PDF encoding issues
    text = text.replace("­‐‑", "-")  # Replace garbled dashes (soft hyphen + hyphens)
    text = text.replace("­‐", "-")
    text = text.replace("‑", "-")
    text = text.replace("–", "-")  # en-dash
    text = text.replace("—", "--")  # em-dash
    # Smart quotes → ASCII. The previous form `text.replace("'", "'")` was
    # source-mangled (both sides ASCII U+0027) and silently became a no-op;
    # use explicit Unicode escapes so the substitution is unambiguous and
    # cannot regress through a future copy-paste through a smart-quote system.
    text = text.replace("\u2018", "'")  # left single quotation mark
    text = text.replace("\u2019", "'")  # right single quotation mark
    text = text.replace("\u201b", "'")  # single high-reversed-9 quotation mark
    text = text.replace("\u201c", '"')  # left double quotation mark
    text = text.replace("\u201d", '"')  # right double quotation mark

    # Normalize all whitespace sequences to single space
    text = re.sub(r"\s+", " ", text)
    text = _stitch_hyphen_line_breaks(text)
    return text.strip()


def polish_text(text: str | None) -> str | None:
    """Clean OCR artifacts, spacing, and boilerplate from text fields."""

    if text is None:
        return None

    cleaned = text
    for pattern in _LEGENDARY_SENTENCES:
        cleaned = pattern.sub("", cleaned)

    # Strip the PDF page footer (mirrors clean_text). Monster trait/action
    # descriptions flow through polish_text rather than clean_text, so the
    # strip has to live here as well.
    cleaned = strip_srd_page_footer(cleaned)

    cleaned = cleaned.replace("\u2013", "—").replace("\u2014", "—")
    cleaned = re.sub(r"--+", "—", cleaned)
    cleaned = re.sub(r"\bH\s*it\b", "Hit", cleaned)
    cleaned = re.sub(r"Hit:\s*(\d)", r"Hit: \1", cleaned)
    cleaned = re.sub(r"(\d+d\d+)\s*([+-])\s*(\d+)", r"\1 \2 \3", cleaned)
    cleaned = cleaned.replace("keepsgoing", "keeps going")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = _stitch_hyphen_line_breaks(cleaned)
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
