"""Low-level PDF text-probe helpers.

This module is intentionally tiny: open a PDF, pull text from a page or
range of pages, and apply the SRD-specific whitespace normalization that
turns extraction output from "looks corrupted" into "perfectly readable".

It is the shared primitive for:
  - reproducer tests in tests/test_pdf_provenance.py (probing claims that
    a region is "corrupted")
  - future real extractors (extract_lineages.py,
    extract_spell_classes.py) that retire hand-curated *_targets.py
    modules

The function set is deliberately small. Anything beyond "give me text
from this page" belongs in a higher-level extractor that consumes this.

Page indices are 0-based (PyMuPDF convention). Translate from SRD page
numbers via utils.page_index.PAGE_INDEX, which is 1-based.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import fitz

# SRD body text uses tab + carriage-return + non-breaking-space sequences
# as word separators rather than ordinary spaces. Collapsing them into
# a single space is what makes "corrupted" text suddenly readable.
_WS_SEPARATORS = re.compile(r"[\t\r\xa0]+")
_WS_RUNS = re.compile(r"\s+")


def normalize_whitespace(text: str) -> str:
    """Collapse SRD's tab+CR+nbsp word separators into single spaces."""
    text = _WS_SEPARATORS.sub(" ", text)
    return _WS_RUNS.sub(" ", text).strip()


@contextmanager
def open_pdf(pdf_path: Path) -> Iterator[fitz.Document]:
    """Context-managed PDF open. Lets callers `with open_pdf(p) as doc:`."""
    import fitz

    doc = fitz.open(str(pdf_path))
    try:
        yield doc
    finally:
        doc.close()


def page_text(doc: fitz.Document, pdf_index: int, *, normalize: bool = True) -> str:
    """Return text for a single page (0-based PDF index)."""
    raw = doc.load_page(pdf_index).get_text("text")
    return normalize_whitespace(raw) if normalize else raw


def pages_text(
    doc: fitz.Document,
    pdf_indices: range | list[int],
    *,
    normalize: bool = True,
) -> dict[int, str]:
    """Return {pdf_index: text} for the given page indices."""
    return {idx: page_text(doc, idx, normalize=normalize) for idx in pdf_indices}


def page_dict(doc: fitz.Document, pdf_index: int, *, flags: int = 0) -> dict:
    """Return PyMuPDF's structured "dict" output for a page (0-based index).

    Used by extractors that need font/bbox/span metadata in addition to
    plain text (e.g. font-fingerprint walks for rules and stat blocks).
    The default ``flags=0`` matches the legacy call sites; pass a
    PyMuPDF ``TEXT_*`` flag set to opt into ligature/whitespace
    preservation.
    """
    return doc.load_page(pdf_index).get_text("dict", flags=flags)


def srd_page_to_pdf_index(srd_page: int) -> int:
    """Convert a 1-based SRD page number to a 0-based PyMuPDF index.

    SRD page 1 (the legal/title page) is PDF index 0.
    """
    return srd_page - 1


def pdf_sha256(pdf_path: Path, *, chunk_size: int = 8192) -> str:
    """Return hex SHA-256 of ``pdf_path`` for provenance/determinism stamps."""
    sha256 = hashlib.sha256()
    with open(pdf_path, "rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def concat_pages_with_offsets(
    doc: fitz.Document,
    pages: Sequence[int],
    *,
    normalize: Callable[[str], str],
    separator: str = " ",
) -> tuple[str, list[tuple[int, int]]]:
    """Concatenate normalized text from ``pages`` of ``doc`` into one
    string, returning the concatenation plus an offset index that maps
    each page's starting char-position back to its 1-indexed page label.

    ``pages`` are 1-indexed PDF page labels; internally each is loaded
    via ``page_text(doc, page - 1, normalize=False)``. ``normalize`` is
    then applied to each page's raw text — callers control whitespace
    policy, soft-hyphen handling, footer stripping, etc.

    The returned ``page_starts: list[(char_offset, page_label)]`` is
    designed to be consumed by :func:`offset_to_page`. Offsets count
    the inserted ``separator`` so reverse-lookups remain exact across
    page boundaries.
    """
    parts: list[str] = []
    page_starts: list[tuple[int, int]] = []
    cursor = 0
    for pdf_page in pages:
        raw = page_text(doc, pdf_page - 1, normalize=False)
        normalized = normalize(raw)
        page_starts.append((cursor, pdf_page))
        parts.append(normalized)
        cursor += len(normalized) + len(separator)
    return separator.join(parts), page_starts


def offset_to_page(page_starts: Sequence[tuple[int, int]], offset: int) -> int:
    """Reverse-map a character offset to its source page label.

    ``page_starts`` must be the second element returned by
    :func:`concat_pages_with_offsets`. Returns the page label whose
    slice contains ``offset``; if ``offset`` precedes the first page
    start, the first page's label is returned.
    """
    page = page_starts[0][1]
    for start, pdf_page in page_starts:
        if start <= offset:
            page = pdf_page
        else:
            break
    return page
