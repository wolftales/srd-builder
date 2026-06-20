"""Shared helpers used by multiple pattern engines.

Span predicates, attach resolvers, span/block transforms, structural
text patterns, PyMuPDF span flag bits, body-cleanup name resolution.
Keep this file dependency-free relative to per-pattern modules.
"""

from __future__ import annotations

from typing import Any

from ...utils.pdf_layout import (
    SPAN_FLAG_BOLD,
    SPAN_FLAG_ITALIC,
    span_matches_predicate,
)

_DEFAULT_STRUCTURAL_PATTERNS = (
    r"^System Reference Document",
    r"^\d+$",
    r"^The [A-Z][a-z]+ Table",
    r"^Level\s+Proficiency",
    r"^Spell Slots per Spell Level",
)

# Re-exported as private aliases so existing imports inside this package
# (e.g. ``from ._shared import _SPAN_FLAG_BOLD``) keep working without
# repeating the magic numbers; the canonical definitions live in
# ``utils.pdf_layout``.
_SPAN_FLAG_ITALIC = SPAN_FLAG_ITALIC
_SPAN_FLAG_BOLD = SPAN_FLAG_BOLD


def _span_matches_fingerprint(span: dict[str, Any], fp: dict[str, Any]) -> bool:
    """Test a single span against a header fingerprint config.

    Thin wrapper around ``utils.pdf_layout.span_matches_predicate`` that
    enforces the legacy fingerprint contract: ``size_min``,
    ``size_max``, and ``font_substring`` are required keys (raises
    ``KeyError`` if missing). The public helper treats them as optional.
    """
    # Touch the required keys so a missing one raises the same KeyError
    # the legacy implementation did.
    _ = (fp["size_min"], fp["size_max"], fp["font_substring"])
    return span_matches_predicate(span, fp)


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
    """Generalized span predicate. Delegates to the public helper in
    ``utils.pdf_layout`` so the engine and the unbound dataset
    extractors share one matcher.
    """
    return span_matches_predicate(span, pred)


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
