"""Shared helpers used by multiple pattern engines.

Span predicates, attach resolvers, span/block transforms, structural
text patterns, PyMuPDF span flag bits, body-cleanup name resolution.
Keep this file dependency-free relative to per-pattern modules.
"""

from __future__ import annotations

from typing import Any

_DEFAULT_STRUCTURAL_PATTERNS = (
    r"^System Reference Document",
    r"^\d+$",
    r"^The [A-Z][a-z]+ Table",
    r"^Level\s+Proficiency",
    r"^Spell Slots per Spell Level",
)

_SPAN_FLAG_ITALIC = 2**1
_SPAN_FLAG_BOLD = 2**4


def _span_matches_fingerprint(span: dict[str, Any], fp: dict[str, Any]) -> bool:
    """Test a single span against a header fingerprint config."""
    text = span["text"].strip()
    if len(text) < fp.get("min_text_len", 1):
        return False
    if fp.get("require_trailing_period", False) and not text.endswith("."):
        return False

    size = span.get("size", 0)
    if not (fp["size_min"] <= size <= fp["size_max"]):
        return False

    font = span.get("font", "")
    if fp["font_substring"] not in font:
        return False

    flags = span.get("flags", 0)
    if fp.get("require_bold", False) and not (flags & _SPAN_FLAG_BOLD):
        return False
    if fp.get("require_italic", False) and not (flags & _SPAN_FLAG_ITALIC):
        return False

    return True


def _resolve_body_cleanup(name: str | None) -> Any:
    """Resolve a body_cleanup config name to a callable. None → identity."""
    if name is None:
        return lambda s: s
    if name == "clean_text":
        from ...utils.prose import clean_text

        return clean_text
    raise ValueError(f"Unknown body_cleanup '{name}'")


def _simplify_span(span: dict[str, Any]) -> dict[str, Any]:
    """Convert a PyMuPDF span dict into the simplified per-bucket form used by
    font_split_spans body_grouping. Shape: {text, font, size, is_bold, is_italic}.
    """
    font = span.get("font", "")
    return {
        "text": span.get("text", ""),
        "font": font,
        "size": round(span.get("size", 0), 1),
        "is_bold": "Bold" in font or "SemiBold" in font,
        "is_italic": "Italic" in font,
    }


def _span_matches_predicate(span: dict[str, Any], pred: dict[str, Any]) -> bool:
    """Generalized span predicate. All keys optional; absent keys are not
    constraints. Empty predicate {} matches every span.
    """
    text = span.get("text", "").strip()
    if "min_text_len" in pred and len(text) < pred["min_text_len"]:
        return False
    if pred.get("require_trailing_period", False) and not text.endswith("."):
        return False
    size = span.get("size", 0)
    if "size_min" in pred and size < pred["size_min"]:
        return False
    if "size_max" in pred and size > pred["size_max"]:
        return False
    if "font_substring" in pred and pred["font_substring"] not in span.get("font", ""):
        return False
    flags = span.get("flags", 0)
    if pred.get("require_bold", False) and not (flags & _SPAN_FLAG_BOLD):
        return False
    if pred.get("require_italic", False) and not (flags & _SPAN_FLAG_ITALIC):
        return False
    return True


def _resolve_attach(attach: dict[str, Any], font: str) -> dict[str, Any]:
    """Resolve attach-dict values, replacing sentinel strings with computed
    booleans from the span's font name. Recognised sentinels:
        "$bold_from_font"   → "Bold" in font or "SemiBold" in font
        "$italic_from_font" → "Italic" in font
    """
    out: dict[str, Any] = {}
    for k, v in attach.items():
        if v == "$bold_from_font":
            out[k] = ("Bold" in font) or ("SemiBold" in font)
        elif v == "$italic_from_font":
            out[k] = "Italic" in font
        else:
            out[k] = v
    return out


def _make_span_block(span: dict[str, Any], attach: dict[str, Any]) -> dict[str, Any]:
    """Build the per-bucket span dict: {text, font, size} + resolved attach.

    Text is stripped to match the bespoke-extractor convention where the
    same stripped value populates both subfields and bucketed spans.
    """
    font = span.get("font", "")
    block: dict[str, Any] = {
        "text": span.get("text", "").strip(),
        "font": font,
        "size": round(span.get("size", 0), 1),
    }
    block.update(_resolve_attach(attach, font))
    return block


def _bucket_text(record: dict[str, Any], bucket: str) -> str:
    return " ".join(s.get("text", "") for s in record.get(bucket, []))
