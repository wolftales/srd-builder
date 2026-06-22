"""PDF layout primitives: bbox math, column detection, span/line merging.

These helpers were extracted from extract_monsters.py to make column-aware
span extraction reusable by other PDF dataset extractors. They are intended
as low-level building blocks, not a full extraction pipeline — callers
remain responsible for opening the PDF (via utils.pdf_probe.open_pdf) and
for any domain-specific span/line interpretation.

Span-dict shape (what these helpers produce and consume):

    {
        "page": int,                 # 1-based page number
        "column": int,               # 0 single / 1 left / 2 right
        "bbox": [x0, y0, x1, y1],    # rounded to 2 decimals
        "text": str,                 # span text (stripped)
        "font": str,                 # PyMuPDF font name
        "size": float,               # font size, rounded to 2 decimals
        "color": list[int],          # [r, g, b] 0..255
        "flags": int,                # PyMuPDF span flags
    }

Line-dict shape (output of `merge_spans_into_lines`) has the same fields
plus a "spans" list with the originals.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import fitz

from .pdf_probe import normalize_whitespace

Y_COORDINATE_TOLERANCE = 2.0
FONT_SIZE_TOLERANCE = 0.5

# PyMuPDF span flag bits. Mirrored as public constants so callers don't
# repeat the magic numbers; see PyMuPDF docs for the full bitfield.
SPAN_FLAG_ITALIC = 2**1  # 2
SPAN_FLAG_BOLD = 2**4  # 16


def is_bold(flags: int) -> bool:
    """True if the PyMuPDF span ``flags`` bitfield marks the span as bold."""
    return bool(flags & SPAN_FLAG_BOLD)


def is_italic(flags: int) -> bool:
    """True if the PyMuPDF span ``flags`` bitfield marks the span as italic."""
    return bool(flags & SPAN_FLAG_ITALIC)


def iter_page_spans(page_dict: dict[str, Any]) -> Any:
    """Yield raw PyMuPDF span dicts from a ``page.get_text('dict')`` payload.

    Walks the canonical block → line → span structure and skips non-text
    blocks (``block['type'] != 0``). Callers receive the original span
    dict references, so any per-span normalization (whitespace,
    rounding) remains the caller's responsibility.

    Lifted out of the triple-loop boilerplate that previously appeared
    in extract_lineages, extract_rules, extract_spell_classes, etc.
    """
    for block in page_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            yield from line.get("spans", [])


def iter_normalized_spans(page: fitz.Page) -> Any:
    """Yield ``(span, text)`` pairs from a page, skipping empty-text spans.

    Wraps ``iter_page_spans(page.get_text('dict'))`` and applies
    ``utils.pdf_probe.normalize_whitespace`` to each span's text. Spans
    whose text is empty after normalization are filtered out — this
    matches what every font-classifier caller (lineages, spell_classes,
    classes) needs as the first step inside the span loop, so they no
    longer need to open-code the ``get_text('dict')`` + whitespace
    normalize + ``if not text: continue`` triplet themselves.

    The yielded ``span`` is the original PyMuPDF span dict (with its
    raw ``text`` field unchanged); the yielded ``text`` is the
    whitespace-normalized form for predicates and downstream storage.
    Callers that need the span dict to carry the normalized text should
    rewrite it with ``{**span, "text": text}`` (mirrors what
    extract_lineages does so its ``span_matches_predicate`` sees the
    same string it'll store).
    """
    for span in iter_page_spans(page.get_text("dict")):
        text = normalize_whitespace(span["text"])
        if not text:
            continue
        yield span, text


def span_matches_predicate(span: dict[str, Any], predicate: dict[str, Any]) -> bool:
    """Test a PyMuPDF span against a declarative predicate dict.

    All predicate keys are optional; absent keys impose no constraint
    (so ``{}`` matches any span). Recognised keys:

      - ``min_text_len`` (int): minimum stripped-text length
      - ``require_trailing_period`` (bool): text must end with ``.``
      - ``size_min`` / ``size_max`` (float): inclusive font-size range
      - ``font_substring`` (str): substring required in the font name
      - ``font_exact`` (str): exact match required on the font name
      - ``require_bold`` (bool): span flags must include the bold bit
      - ``require_italic`` (bool): span flags must include the italic bit

    The matcher reads ``span['text']`` verbatim (no normalization), so
    callers that pre-normalize text should pass a copy of the span dict
    with the normalized text in place.
    """
    text = span.get("text", "").strip()
    if "min_text_len" in predicate and len(text) < predicate["min_text_len"]:
        return False
    if predicate.get("require_trailing_period", False) and not text.endswith("."):
        return False
    size = span.get("size", 0)
    if "size_min" in predicate and size < predicate["size_min"]:
        return False
    if "size_max" in predicate and size > predicate["size_max"]:
        return False
    font = span.get("font", "")
    if "font_substring" in predicate and predicate["font_substring"] not in font:
        return False
    if "font_exact" in predicate and font != predicate["font_exact"]:
        return False
    flags = span.get("flags", 0)
    if predicate.get("require_bold", False) and not (flags & SPAN_FLAG_BOLD):
        return False
    if predicate.get("require_italic", False) and not (flags & SPAN_FLAG_ITALIC):
        return False
    return True


def find_in_lookahead(
    items: Sequence[dict[str, Any]],
    anchor_index: int,
    validator: Callable[[dict[str, Any]], bool],
    *,
    max_items: int = 20,
    stop_when: Callable[[dict[str, Any], dict[str, Any]], bool] | None = None,
) -> int | None:
    """Scan forward from ``items[anchor_index + 1]`` for the first item that
    passes ``validator``. Return its index, or ``None`` if no match is
    found within the lookahead window.

    ``max_items`` caps how many candidates are examined. ``stop_when``
    receives ``(anchor, candidate)`` and may terminate the scan early
    (e.g. when geometric distance exceeds a threshold). Both predicates
    are called per candidate; ``stop_when`` is checked first.

    The function makes no assumptions about item shape beyond what the
    caller's predicates need. Useful for anchor + following-token
    validation patterns (e.g. monster-name → size/type line lookahead)
    that scan a flat line/span sequence.
    """
    if anchor_index < 0 or anchor_index >= len(items) - 1:
        return None
    anchor = items[anchor_index]
    end = min(anchor_index + 1 + max_items, len(items))
    for i in range(anchor_index + 1, end):
        candidate = items[i]
        if stop_when is not None and stop_when(anchor, candidate):
            return None
        if validator(candidate):
            return i
    return None


def cluster_values_by_gap(
    values: Iterable[float],
    *,
    max_gap: float,
) -> list[list[float]]:
    """Group a flat set of numeric values into clusters where neighbors
    within a cluster are at most ``max_gap`` apart.

    Inputs are de-duplicated and sorted before clustering. Returns a list
    of clusters (each a sorted ``list[float]``); empty input yields
    ``[]``. The clustering is greedy on the sorted sequence: a new
    cluster starts whenever the gap to the previous value exceeds
    ``max_gap``.

    Useful for detecting columns or rows from bbox coordinates where
    intra-group spacing is small and inter-group spacing is large
    (e.g. the left/right columns of a two-column SRD page where cells
    within a column sit within a few points of each other but columns
    are >>100pt apart).
    """
    sorted_unique = sorted(set(values))
    if not sorted_unique:
        return []
    clusters: list[list[float]] = [[sorted_unique[0]]]
    for v in sorted_unique[1:]:
        if v - clusters[-1][-1] > max_gap:
            clusters.append([v])
        else:
            clusters[-1].append(v)
    return clusters


def color_to_rgb(color_int: int) -> list[int]:
    """Convert a PyMuPDF packed color integer into [r, g, b]."""
    return [(color_int >> 16) & 0xFF, (color_int >> 8) & 0xFF, color_int & 0xFF]


def merge_bboxes(b1: list[float], b2: list[float]) -> list[float]:
    """Union two PyMuPDF bboxes [x0, y0, x1, y1]."""
    return [
        min(b1[0], b2[0]),
        min(b1[1], b2[1]),
        max(b1[2], b2[2]),
        max(b1[3], b2[3]),
    ]


def determine_column(x: float, *, midpoint: float | None) -> int:
    """Return column id given a left-edge x coordinate.

    midpoint=None means treat as single-column → always 0.
    Otherwise: 1 (left) if x < midpoint, else 2 (right).
    """
    if midpoint is None:
        return 0
    return 1 if x < midpoint else 2


def extract_columnar_spans(
    page: fitz.Page,
    page_num: int,
    *,
    column_midpoint: float | None,
    header_size_min: float = 13.0,
) -> list[dict[str, Any]]:
    """Extract text spans from a page with column + bbox metadata.

    Spans are sorted in reading order: (page, column, top-y, left-x).
    """
    textpage = page.get_textpage(flags=fitz.TEXTFLAGS_TEXT)
    page_dict = page.get_text("dict", textpage=textpage)

    spans: list[dict[str, Any]] = []
    for block in page_dict.get("blocks", []):
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                bbox = span.get("bbox", [0, 0, 0, 0])
                size = round(span.get("size", 0), 2)
                spans.append(
                    {
                        "page": page_num,
                        "column": determine_column(bbox[0], midpoint=column_midpoint),
                        "bbox": [round(x, 2) for x in bbox],
                        "text": text,
                        "font": span.get("font", ""),
                        "size": size,
                        "color": color_to_rgb(span.get("color", 0)),
                        "flags": span.get("flags", 0),
                        "is_header": size >= header_size_min,
                    }
                )

    spans.sort(key=lambda s: (s["page"], s["column"], s["bbox"][1], s["bbox"][0]))
    return spans


def merge_spans_into_lines(
    spans: list[dict[str, Any]],
    *,
    y_tolerance: float = Y_COORDINATE_TOLERANCE,
    size_tolerance: float = FONT_SIZE_TOLERANCE,
) -> list[dict[str, Any]]:
    """Merge consecutive spans that occupy the same logical line.

    Two spans belong to the same line iff:
      - same page and column
      - top-y differs by no more than y_tolerance
      - same font, with size within size_tolerance
    """
    if not spans:
        return []

    lines: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for span in spans:
        if current is not None and _on_same_line(current, span, y_tolerance, size_tolerance):
            current["text"] += " " + span["text"]
            current["spans"].append(span)
            current["bbox"] = merge_bboxes(current["bbox"], span["bbox"])
            continue
        if current is not None:
            lines.append(current)
        current = {
            "page": span["page"],
            "column": span["column"],
            "bbox": span["bbox"].copy(),
            "text": span["text"],
            "font": span["font"],
            "size": span["size"],
            "color": span["color"],
            "flags": span["flags"],
            "is_header": span.get("is_header", False),
            "spans": [span],
        }

    if current is not None:
        lines.append(current)
    return lines


def _on_same_line(
    line: dict[str, Any],
    span: dict[str, Any],
    y_tolerance: float,
    size_tolerance: float,
) -> bool:
    if line["page"] != span["page"] or line["column"] != span["column"]:
        return False
    if abs(line["bbox"][1] - span["bbox"][1]) > y_tolerance:
        return False
    if line["font"] != span["font"]:
        return False
    if abs(line["size"] - span["size"]) > size_tolerance:
        return False
    return True
