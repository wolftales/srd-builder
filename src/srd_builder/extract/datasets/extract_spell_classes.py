"""Extract spell-to-class associations from SRD 5.1 PDF pages 105-113.

Replaces the hand-curated ``rulesets/srd_5_1/spell_class_targets.py``
(~917 lines, ~888 of which are 8 alphabetised spell lists). The "PDF
text is corrupted" rationale on that file was disproven by
[tests/test_pdf_provenance.py::test_spell_lists_pages_class_headers_are_extractable](../../../tests/test_pdf_provenance.py).

Font fingerprints on pages 105-113 (verified 2026-06-17 against
SRD_CC_v5.1.pdf via PyMuPDF 1.27.x):

- 18.0pt GillSans-SemiBold    — section header "Spell Lists" (skip)
- 13.9pt GillSans-SemiBold    — class section header
                                ("Bard Spells" ... "Wizard Spells"; 8 hits)
- 12.0pt GillSans-SemiBold    — spell-level header
                                ("Cantrips (0 Level)", "1st Level", ...; 70 hits)
- 9.8pt  Cambria              — spell name (~778 hits, the spell list contents)
- 10.8pt GillSans-SemiBold/   — page number + "System Reference Document 5.1"
        Calibri                  footer (skip)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz

from srd_builder.postprocess.ids import normalize_id
from srd_builder.utils.pdf_layout import iter_normalized_spans, span_matches_predicate

SPELL_LIST_PAGES_PDF_INDICES = range(104, 113)  # SRD pages 105-113

# Canonical class section header → ruleset class name. The PDF labels them
# exactly as below; the value is what postprocess.spells emits in the
# ``classes`` list on each spell record (lowercase, alphabetical).
_CLASS_HEADERS = {
    "Bard Spells": "bard",
    "Cleric Spells": "cleric",
    "Druid Spells": "druid",
    "Paladin Spells": "paladin",
    "Ranger Spells": "ranger",
    "Sorcerer Spells": "sorcerer",
    "Warlock Spells": "warlock",
    "Wizard Spells": "wizard",
}

# Spell-level headers we skip (they live at the same font size as spell
# names on a few PDF pages? No — 12pt G-SB vs 9.8pt Cambria, so the font
# classifier handles them. This set documents the exhaustive list.)
_LEVEL_HEADER_PATTERN = re.compile(
    r"^(Cantrips?\s*\(0\s*Level\)|\d+(?:st|nd|rd|th)\s+Level)$",
    re.IGNORECASE,
)

# Font fingerprints fed to ``span_matches_predicate``. The class-header
# rule selects the per-class banner that resets ``current_class``; the
# remaining rules are skip filters (level dividers, the "Spell Lists"
# page header, page numbers); the spell-name rule selects the entries
# we actually collect.
_PRED_CLASS_HEADER = {
    "size_min": 13.5,
    "size_max": 14.5,
    "font_substring": "GillSans",
    "require_bold": True,
}
_PRED_LEVEL_HEADER = {
    "size_min": 11.5,
    "size_max": 12.5,
    "font_substring": "GillSans",
    "require_bold": True,
}
_PRED_PAGE_HEADER = {
    "size_min": 17.5,
    "font_substring": "GillSans",
}
_PRED_SPELL_NAME = {
    "size_min": 9.5,
    "size_max": 10.5,
    "font_substring": "Cambria",
}


def extract_spell_classes(pdf_path: str | Path) -> dict[str, Any]:
    """Extract the spell→class mapping from the SRD PDF.

    Returns a dict shaped::

        {
            "source_pages": "105-113",
            "class_spells": {
                "bard": ["dancing_lights", "light", ...],
                "cleric": [...],
                ...
            },
        }

    where each list contains ``simple_name`` strings (snake_case, matching
    the convention used by :mod:`srd_builder.postprocess.ids.normalize_id`).
    Lists are returned in PDF order (Cantrips first, then 1st Level, etc.,
    each level alphabetical as printed in the PDF).
    """
    pdf_path = Path(pdf_path)
    class_spells: dict[str, list[str]] = {name: [] for name in _CLASS_HEADERS.values()}
    current_class: str | None = None

    with fitz.open(str(pdf_path)) as doc:
        for pi in SPELL_LIST_PAGES_PDF_INDICES:
            page = doc[pi]
            for span, text in iter_normalized_spans(page):
                size = round(span.get("size", 0), 1)

                # 13.9pt G-SB = class header
                if span_matches_predicate(span, _PRED_CLASS_HEADER):
                    cls = _CLASS_HEADERS.get(text)
                    if cls:
                        current_class = cls
                    continue

                # 12.0pt G-SB = level header (just a divider; skip)
                if span_matches_predicate(span, _PRED_LEVEL_HEADER):
                    continue

                # 18.0pt G-SB = "Spell Lists" (skip)
                if span_matches_predicate(span, _PRED_PAGE_HEADER):
                    continue

                # 10.8pt = page numbers / footer (skip)
                if 10.5 <= size <= 11.0:
                    continue

                # 9.8pt Cambria = spell name
                if current_class and span_matches_predicate(span, _PRED_SPELL_NAME):
                    simple = normalize_id(text)
                    if simple and simple not in class_spells[current_class]:
                        class_spells[current_class].append(simple)

    return {
        "source_pages": "105-113",
        "class_spells": class_spells,
    }


def build_spell_to_classes_map(class_spells: dict[str, list[str]]) -> dict[str, list[str]]:
    """Invert a class→[spells] mapping into a spell→[classes] mapping.

    The returned dict is the form :mod:`srd_builder.postprocess.spells`
    needs: keys are spell ``simple_name`` strings, values are alphabetically
    sorted lists of class names.
    """
    out: dict[str, list[str]] = {}
    for cls, spells in class_spells.items():
        for spell in spells:
            out.setdefault(spell, []).append(cls)
    for classes in out.values():
        classes.sort()
    return out
