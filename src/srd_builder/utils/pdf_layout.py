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

from typing import Any

import fitz

Y_COORDINATE_TOLERANCE = 2.0
FONT_SIZE_TOLERANCE = 0.5


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
