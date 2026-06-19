"""Extract bold-headed prose item descriptions from the SRD equipment chapter.

Replaces the four hand-curated literals
(`ADVENTURE_GEAR_DESCRIPTIONS`, `TOOLS_DESCRIPTIONS`, `ARMOR_DESCRIPTIONS`,
`LIFESTYLE_DESCRIPTIONS`) in
`src/srd_builder/assemble/equipment_descriptions.py` (~398 lines) with a
live parser over PDF pages 63, 66-68, 70-71, 73.

The reproducer at
[tests/test_pdf_provenance.py::test_equipment_descriptions_section_anchor_extractable](../../../../tests/test_pdf_provenance.py)
(parametrized x 4) plus
[tests/test_pdf_provenance.py::test_equipment_descriptions_item_signature_extractable](../../../../tests/test_pdf_provenance.py)
(parametrized x 13) proved each section's heading + content is recoverable
under standard whitespace normalization. The only extra work the parser
does on top of that is collapsing PDF soft-hyphen sequences
(`U+00AD U+2010 U+2011`) inside compound words like `15-foot`.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, TypedDict

from srd_builder.utils.page_index import PAGE_INDEX
from srd_builder.utils.pdf_probe import open_pdf, page_text

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "0.27.6"


class ItemDescription(TypedDict):
    item_id: str
    description: str
    page: int


# ---------------------------------------------------------------------------
# Section configuration
# ---------------------------------------------------------------------------

# (section_label, [pdf_page_1_indexed, ...])
# Pages are 1-indexed SRD page labels; iteration uses (page - 1) for the
# 0-indexed pymupdf document.
_SECTIONS: list[tuple[str, list[int]]] = [
    ("armor", [63]),
    ("adventuring_gear", [66, 67, 68]),
    ("tools", [70, 71]),
    ("lifestyle", [73]),
]


# Curated item_id mapping. The key is the exact PDF heading text (after
# whitespace and soft-hyphen normalization) up to and including the
# trailing period. The value is the stable item_id that downstream
# consumers (`assemble_equipment.py`) already use.
#
# Order matters only for `_meta.descriptions_extracted`; the parser
# returns descriptions in PDF reading order, not in this dict's order.
_HEADING_TO_ITEM_ID: dict[str, str] = {
    # Armor (p. 63) — 12 entries
    "Padded.": "item:padded",
    "Leather.": "item:leather",
    "Studded Leather.": "item:studded-leather",
    "Hide.": "item:hide",
    "Chain Shirt.": "item:chain-shirt",
    "Scale Mail.": "item:scale-mail",
    "Breastplate.": "item:breastplate",
    "Half Plate.": "item:half-plate",
    "Ring Mail.": "item:ring-mail",
    "Chain Mail.": "item:chain-mail",
    "Splint.": "item:splint",
    "Plate.": "item:plate",
    # Adventure Gear (pp. 66-68) — 42 entries
    "Acid.": "item:acid-vial",
    "Alchemist's Fire.": "item:alchemists-fire-flask",
    "Antitoxin.": "item:antitoxin-vial",
    "Arcane Focus.": "item:arcane-focus",
    "Ball Bearings.": "item:ball-bearings-bag-of-1000",
    "Block and Tackle.": "item:block-and-tackle",
    "Book.": "item:book",
    "Caltrops.": "item:caltrops-bag-of-20",
    "Candle.": "item:candle",
    "Case, Crossbow Bolt.": "item:case-crossbow-bolt",
    "Case, Map or Scroll.": "item:case-map-or-scroll",
    "Chain.": "item:chain-10-feet",
    "Climber's Kit.": "item:climbers-kit",
    "Component Pouch.": "item:component-pouch",
    "Crowbar.": "item:crowbar",
    "Druidic Focus.": "item:druidic-focus",
    "Fishing Tackle.": "item:fishing-tackle",
    "Healer's Kit.": "item:healers-kit",
    "Holy Symbol.": "item:holy-symbol",
    "Holy Water.": "item:holy-water-flask",
    "Hunting Trap.": "item:hunting-trap",
    "Lamp.": "item:lamp",
    "Lantern, Bullseye.": "item:lantern-bullseye",
    "Lantern, Hooded.": "item:lantern-hooded",
    "Lock.": "item:lock",
    "Magnifying Glass.": "item:magnifying-glass",
    "Manacles.": "item:manacles",
    "Mess Kit.": "item:mess-kit",
    "Oil.": "item:oil-flask",
    "Poison, Basic.": "item:poison-basic-vial",
    "Potion of Healing.": "item:potion-of-healing",
    "Pouch.": "item:pouch",
    "Quiver.": "item:quiver",
    "Ram, Portable.": "item:ram-portable",
    "Rations.": "item:rations-1-day",
    "Rope.": "item:rope-hempen-50-feet",
    "Scale, Merchant's.": "item:scale-merchants",
    "Spellbook.": "item:spellbook",
    "Spyglass.": "item:spyglass",
    "Tent.": "item:tent",
    "Tinderbox.": "item:tinderbox",
    "Torch.": "item:torch",
    # Tools (pp. 70-71) — 9 entries
    "Artisan's Tools.": "item:artisans-tools",
    "Disguise Kit.": "item:disguise-kit",
    "Forgery Kit.": "item:forgery-kit",
    "Gaming Set.": "item:gaming-set",
    "Herbalism Kit.": "item:herbalism-kit",
    "Musical Instrument.": "item:musical-instrument",
    "Navigator's Tools.": "item:navigators-tools",
    "Poisoner's Kit.": "item:poisoners-kit",
    "Thieves' Tools.": "item:thieves-tools",
    # Lifestyle (p. 73) — 6 entries
    # NOTE: 'Wretched.' (also on p. 73) is deliberately omitted — the
    # SRD lifestyle cost table has no row for it, so the retired
    # `LIFESTYLE_DESCRIPTIONS` literal scoped it out. Preserved here for
    # backward-compatibility; remove from this skip-list if downstream
    # ever grows a Wretched cost row.
    "Squalid.": "item:squalid",
    "Poor.": "item:poor",
    "Modest.": "item:modest",
    "Comfortable.": "item:comfortable",
    "Wealthy.": "item:wealthy",
    "Aristocratic.": "item:aristocratic",
}


# Heading anchor regex. Picks up a Title-Case word (possibly with
# embedded apostrophe/comma/space) followed by a period and at least one
# space and a capital letter. Run over normalized text so the soft-
# hyphen artifacts are already gone.
#
# Title Case in the SRD uses lowercase joining words ("and", "or", "of"),
# so the regex allows a small set of lowercase glue words between the
# capitalized tokens (e.g., "Block and Tackle.", "Case, Map or Scroll.",
# "Potion of Healing.").
#
# Over-matches are EXPECTED — `_HEADING_TO_ITEM_ID` is the filter. The
# regex's job is to find every candidate so we don't miss a heading;
# the table's job is to decide which candidates are real item headings.
_HEADING_RE = re.compile(
    r"(?<=[\s.])"  # preceded by whitespace or sentence-ending period
    r"("
    r"[A-Z][A-Za-z',]+"  # first Title-Case word
    r"(?:[ ,]+(?:[A-Z][A-Za-z']+|and|or|of))*"  # optional ", Word" / " and "
    r"\."  # trailing period
    r")"
    r"(?= [A-Z])"  # followed by space + Capital (paragraph break)
)


_CURLY_APOS = "\u2019"
# Sequence of 2+ hyphen-like characters (PDF soft hyphen U+00AD, hyphen
# U+2010, non-breaking hyphen U+2011, ASCII '-') collapses to a single
# ASCII hyphen. Singletons are preserved so legitimate hyphenated words
# like "narrow-bladed" survive.
_SOFT_HYPHEN_RE = re.compile(r"[-\xad\u2010\u2011]{2,}")
_WHITESPACE_RE = re.compile(r"\s+")
# PDF line-wraps around em-dashes leave a stray space after whitespace
# normalization ("item— an"). The curated SRD typography closes them,
# so do the same on both sides.
_EM_DASH_SPACE_RE = re.compile(r" *— *")
# Running page footer/header rendered by pymupdf into the text stream.
# Strip so descriptions that span page boundaries don't carry the
# "System Reference Document 5.1 67" marker mid-sentence.
_PAGE_FOOTER_RE = re.compile(r"\s*System Reference Document 5\.1 \d+\s*")


def _normalize(text: str) -> str:
    """Collapse soft-hyphen runs, normalize apostrophes + whitespace."""
    text = _SOFT_HYPHEN_RE.sub("-", text)
    text = text.replace(_CURLY_APOS, "'")
    text = _WHITESPACE_RE.sub(" ", text)
    text = _PAGE_FOOTER_RE.sub(" ", text)
    text = _EM_DASH_SPACE_RE.sub("—", text)
    return text.strip()


# Subsection headers that may appear BETWEEN or AFTER item descriptions
# inside a section's concatenated text. When found inside a body slice
# they terminate the body — this stops a description from bleeding into
# the prose intro of the following armor category, the lifestyle
# "Self-Sufficiency" sidebar, the "Mounts and Vehicles" subsection
# after Tools, etc. Order does not matter; the EARLIEST occurrence
# wins.
_SUBSECTION_TERMINATORS: dict[str, tuple[str, ...]] = {
    "armor": (
        # Between Half Plate and Ring Mail (Medium → Heavy transition)
        "Heavy Armor ",
        # Between Studded Leather and Hide (Light → Medium transition)
        "Medium Armor ",
        # After Plate (last armor item) the table repeats: "Armor Armor Cost..."
        "Armor Armor Cost",
    ),
    "adventuring_gear": (
        # Page footer / running header on p.68 after Torch (last item)
        "Adventuring Gear",
    ),
    "tools": (
        # After Thieves' Tools (last tools item) the Mounts subsection begins
        "Mounts and Vehicles",
    ),
    "lifestyle": (
        # After Aristocratic (last lifestyle item) the Self-Sufficiency sidebar
        "Self-Sufficiency",
    ),
}


def _build_section_text(
    pages: list[int],
    doc: Any,
    separator: str = " ",
) -> tuple[str, list[tuple[int, int]]]:
    """Concatenate normalized text of `pages` into one section string.

    Returns:
        (section_text, page_starts) where `page_starts` is a list of
        `(char_offset, page_number)` tuples giving the offset at which
        each page's normalized text begins inside `section_text`. Used
        to attribute the heading match offset back to the source page.
    """
    parts: list[str] = []
    page_starts: list[tuple[int, int]] = []
    cursor = 0
    for pdf_page in pages:
        raw = page_text(doc, pdf_page - 1)
        normalized = _normalize(raw)
        page_starts.append((cursor, pdf_page))
        parts.append(normalized)
        cursor += len(normalized) + len(separator)
    return separator.join(parts), page_starts


def _offset_to_page(offset: int, page_starts: list[tuple[int, int]]) -> int:
    """Map a character offset in section text back to its source page."""
    page = page_starts[0][1]
    for start, pdf_page in page_starts:
        if start <= offset:
            page = pdf_page
        else:
            break
    return page


def _extract_section(
    section_name: str,
    pages: list[int],
    doc: Any,
) -> list[ItemDescription]:
    """Extract every resolving item description from a single section.

    Concatenates the section's pages, runs `_HEADING_RE` over the joined
    text, slices between consecutive resolving matches, then truncates
    each slice at the earliest subsection terminator (if any) found
    inside it.
    """
    section_text, page_starts = _build_section_text(pages, doc)
    matches = list(_HEADING_RE.finditer(section_text))
    resolving = [m for m in matches if m.group(1) in _HEADING_TO_ITEM_ID]
    terminators = _SUBSECTION_TERMINATORS.get(section_name, ())

    records: list[ItemDescription] = []
    for i, m in enumerate(resolving):
        heading = m.group(1)
        item_id = _HEADING_TO_ITEM_ID[heading]
        body_start = m.end()
        body_end = resolving[i + 1].start() if i + 1 < len(resolving) else len(section_text)
        # Truncate at the earliest subsection terminator inside the slice
        for term in terminators:
            idx = section_text.find(term, body_start, body_end)
            if idx != -1 and idx < body_end:
                body_end = idx
        description = section_text[body_start:body_end].strip()
        page = _offset_to_page(m.start(), page_starts)
        records.append(ItemDescription(item_id=item_id, description=description, page=page))
    return records


def extract_equipment_descriptions(pdf_path: Path) -> dict[str, Any]:
    """Extract all 69 bold-headed item descriptions from SRD equipment pages.

    Returns:
        {
            "descriptions": [ItemDescription, ...],     # PDF reading order
            "_meta": {
                "extractor_version": str,
                "descriptions_extracted": int,
                "pages_processed": [63, 66, 67, 68, 70, 71, 73],
                "sections": ["armor", "adventuring_gear", "tools", "lifestyle"],
            },
        }
    """
    equipment_pages = PAGE_INDEX["equipment"]["pages"]
    # Pages 63 (armor) and 73 (lifestyle) bracket the equipment chapter;
    # the entries between them are all inside `PAGE_INDEX["equipment"]`.
    for _section, pages in _SECTIONS:
        for p in pages:
            if not (equipment_pages["start"] <= p <= equipment_pages["end"]):
                raise RuntimeError(
                    f"PAGE_INDEX['equipment'] no longer covers page {p}; "
                    f"extract_equipment_descriptions assumes the equipment "
                    f"chapter covers pp. 63-74."
                )

    all_records: list[ItemDescription] = []
    pages_processed: list[int] = []

    with open_pdf(pdf_path) as doc:
        for section_name, pages in _SECTIONS:
            all_records.extend(_extract_section(section_name, pages, doc))
            pages_processed.extend(pages)

    logger.info(
        "Extracted %d equipment descriptions from PDF pages %s",
        len(all_records),
        pages_processed,
    )

    return {
        "descriptions": all_records,
        "_meta": {
            "extractor_version": EXTRACTOR_VERSION,
            "descriptions_extracted": len(all_records),
            "pages_processed": pages_processed,
            "sections": [s for s, _ in _SECTIONS],
        },
    }
