"""Extract class structures from SRD 5.1 PDF pages 8-55.

Replaces the hand-curated ``rulesets/srd_5_1/class_targets.py`` (~763
lines, in service since v0.8.2). The "manually transcribed via visual
inspection" rationale on that file was disproven by
[tests/test_pdf_provenance.py::test_class_pages_are_extractable_after_whitespace_normalization](../../../tests/test_pdf_provenance.py)
in v0.27.0 (DISPUTED).

Font fingerprints on pages 8-55 (verified 2026-06-18 against
SRD_CC_v5.1.pdf via PyMuPDF 1.27.x using a sample of barbarian p.8):

- 25.9pt GillSans-SemiBold       — class name (12 hits across the range:
                                   Barbarian, Bard, ..., Wizard)
- 18.0pt GillSans-SemiBold       — "Class Features" subheader (one per
                                   class; skip)
- 13.9pt GillSans-SemiBold       — feature heading (e.g. "Rage",
                                   "Unarmored Defense", "Spellcasting")
                                   AND subclass section heading
                                   ("Path of the Berserker",
                                    "College of Lore", "Champion", ...)
- 12.0pt GillSans-SemiBold       — class-block section header
                                   ("Hit Points", "Proficiencies",
                                    "Equipment")
- 12.0pt Calibri-Bold            — progression table title
                                   ("The Barbarian", etc.; skip — the
                                    actual progression rows live in
                                    dist/srd_5_1/tables.json already)
- 9.8pt  Cambria-Bold            — sub-section label
                                   ("Hit Dice:", "Hit Points at 1st
                                    Level:", "Armor:", "Weapons:",
                                    "Tools:", "Saving Throws:",
                                    "Skills:")
- 9.8pt  Cambria                 — body text (accumulate)
- 8.9pt  Calibri / Calibri-Bold  — progression table cells (skip)
- 10.8pt G-SB / Calibri          — page number + footer (skip)

The extractor's output mirrors the legacy ``CLASS_DATA`` consumer
contract for the fields ``parse_classes.py`` + ``parse_features.py``
need. See ``tests/fixtures/srd_5_1/class_targets_snapshot.json`` for
the byte-perfect parity target.

This module is grown incrementally — each commit adds one field group:

1. (v0.27.2 P3 step 1) class discovery: ``name``, ``simple_name``, ``page``
2. proficiencies + hit_die + primary_abilities + saving_throws
3. features list + subclasses
4. spellcasting block
5. progression (mirrored from ``tables.json``)
6. cutover ``parse_classes`` / ``parse_features``, delete
   ``class_targets.py``, retire from PROVENANCE
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from srd_builder.postprocess.ids import normalize_id
from srd_builder.utils.pdf_probe import normalize_whitespace

CLASS_PAGES_PDF_INDICES = range(7, 55)  # SRD pages 8-55 (PDF idx 7-54)

_CLASS_NAME_SIZE = 25.9
_FONT_PREFIX = "GillSans"


def extract_classes(pdf_path: str | Path) -> dict[str, Any]:
    """Extract the 12 SRD 5.1 classes from the PDF.

    Returns a dict shaped (incrementally growing per commit)::

        {
            "source_pages": "8-55",
            "classes": [
                {
                    "name": "Barbarian",
                    "simple_name": "barbarian",
                    "page": 8,
                    # (later commits add hit_die, proficiencies,
                    #  features, subclasses, spellcasting, progression)
                },
                ...
            ],
        }
    """
    pdf_path = Path(pdf_path)
    classes: list[dict[str, Any]] = []

    with fitz.open(str(pdf_path)) as doc:
        for pi in CLASS_PAGES_PDF_INDICES:
            page = doc[pi]
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = normalize_whitespace(span["text"])
                        if not text:
                            continue
                        size = round(span.get("size", 0), 1)
                        font = span.get("font", "")
                        if size != _CLASS_NAME_SIZE or _FONT_PREFIX not in font:
                            continue
                        classes.append(
                            {
                                "name": text,
                                "simple_name": normalize_id(text),
                                "page": pi + 1,
                            }
                        )

    return {"source_pages": "8-55", "classes": classes}
