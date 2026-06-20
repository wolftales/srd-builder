"""Equipment Packs extractor — SRD 5.1 page 70.

Replaces the hand-curated `src/srd_builder/assemble/equipment_packs.py` literal
(323 lines) with a parser that reads the actual SRD PDF.

The page-70 reproducer
([tests/test_pdf_provenance.py::test_equipment_packs_pdf_page_70_*](../../../../tests/test_pdf_provenance.py))
proves all seven pack headers and their comma-separated `Includes …` prose
extract cleanly under standard whitespace normalization. This module turns
that prose into the structured pack records that
`src/srd_builder/assemble/assemble_equipment.py` already consumes, so the
cutover is shape-preserving.

Pipeline:

    PDF page 70  →  whitespace-normalized text  →  per-pack regex split
                                                      ↓
            structured pack dicts  ←  prose tokenizer + phrase→item map
            (name, cost_gp, description, contents)

The `_PHRASE_TO_ITEM` table below is the irreducible normalization layer:
SRD prose phrases ("a hooded lantern", "2 flasks of oil") need to map to
canonical equipment IDs ("item:lantern_hooded", "item:oil_flask"). It is
~30 entries, much smaller than the 323-line literal it replaces, and each
entry is justified by a token in the actual page-70 prose.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, TypedDict

from ...utils.page_index import PAGE_INDEX
from ...utils.pdf_probe import open_pdf, page_text
from ...utils.prose import normalize_apostrophes

logger = logging.getLogger(__name__)

EXTRACTOR_VERSION = "0.27.5"


class PackContents(TypedDict):
    """One item entry inside a pack."""

    item_id: str
    item_name: str
    quantity: int


class EquipmentPack(TypedDict):
    """Structured pack record (matches the retired EQUIPMENT_PACKS shape)."""

    name: str
    cost_gp: int
    description: str
    contents: list[PackContents]
    total_weight_lb: float
    missing_items: list[str]


# Curly apostrophe used by the SRD PDF for possessives (Burglar’s Pack).
_CURLY_APOS = "\u2019"


# --------------------------------------------------------------------------
# Phrase → canonical item lookup.
#
# Each key is the *content phrase* a pack sentence yields after stripping
# the leading article ("a"/"an") or the leading quantity digit. Each value
# is (item_id, item_name, qty_override). qty_override=None means "use the
# parsed leading-digit quantity (or 1 for articled phrases)"; an explicit
# integer means "the digit in the prose is part of the item identity, not
# a quantity multiplier" (e.g., "10 feet of string" is one bundle, not 10
# items).
# --------------------------------------------------------------------------
_PHRASE_TO_ITEM: dict[str, tuple[str, str, int | None]] = {
    # Singular nouns (no transformation other than capitalization)
    "backpack": ("item:backpack", "Backpack", None),
    "bedroll": ("item:bedroll", "Bedroll", None),
    "bell": ("item:bell", "Bell", None),
    "blanket": ("item:blanket", "Blanket", None),
    "censer": ("item:censer", "Censer", None),
    "chest": ("item:chest", "Chest", None),
    "crowbar": ("item:crowbar", "Crowbar", None),
    "hammer": ("item:hammer", "Hammer", None),
    "ink pen": ("item:ink_pen", "Ink pen", None),
    "lamp": ("item:lamp", "Lamp", None),
    "soap": ("item:soap", "Soap", None),
    "tinderbox": ("item:tinderbox", "Tinderbox", None),
    "waterskin": ("item:waterskin", "Waterskin", None),
    # No-article phrases (whole token is the lookup key, q=1)
    "sealing wax": ("item:sealing_wax", "Sealing wax", None),
    "vestments": ("item:vestments", "Vestments", None),
    # Two-word adventurer items
    "alms box": ("item:alms_box", "Alms box", None),
    "book of lore": ("item:book_of_lore", "Book of lore", None),
    "disguise kit": ("item:disguise_kit", "Disguise kit", None),
    "mess kit": ("item:mess_kit", "Mess kit", None),
    # Plurals (parser strips trailing 's' when needed; both forms registered)
    "candles": ("item:candle", "Candle", None),
    "pitons": ("item:piton", "Piton", None),
    "torches": ("item:torch", "Torch", None),
    "costumes": ("item:clothes_costume", "Clothes, costume", None),
    # Phrase rewrites where the SRD prose form ≠ canonical item name
    "hooded lantern": ("item:lantern_hooded", "Lantern, hooded", None),
    "flasks of oil": ("item:oil_flask", "Oil (flask)", None),
    "set of fine clothes": ("item:clothes_fine", "Clothes, fine", None),
    "cases for maps and scrolls": (
        "item:case_map_or_scroll",
        "Case, map or scroll",
        None,
    ),
    "bottle of ink": ("item:ink_1_ounce_bottle", "Ink (1 ounce bottle)", None),
    "vial of perfume": ("item:perfume_vial", "Perfume (vial)", None),
    "sheets of paper": ("item:paper_one_sheet", "Paper (one sheet)", None),
    "sheets of parchment": ("item:parchment_one_sheet", "Parchment (one sheet)", None),
    "little bag of sand": ("item:bag_of_sand_little", "Bag of sand (little)", None),
    "small knife": ("item:knife_small", "Knife (small)", None),
    # Rations: SRD has both "5 days rations" (no "of") and "10 days of rations"
    "days rations": ("item:rations_1_day", "Rations (1 day)", None),
    "days of rations": ("item:rations_1_day", "Rations (1 day)", None),
    # N-bound phrases — the leading digit is part of the item identity, q=1
    "feet of string": ("item:string_10_feet", "String (10 feet)", 1),
    "feet of hempen rope": ("item:rope_hempen_50_feet", "Rope, hempen (50 feet)", 1),
    "bag of 1,000 ball bearings": (
        "item:ball_bearings_bag_of_1000",
        "Ball bearings (bag of 1,000)",
        1,
    ),
    "blocks of incense": ("item:incense_2_blocks", "Incense (2 blocks)", 1),
}


# Pack header on page 70 looks like: "Burglar’s Pack (16 gp). Includes …"
_PACK_HEADER_RE = re.compile(
    r"(?P<name>[A-Z][a-z]+" + _CURLY_APOS + r"s Pack)\s*\((?P<cost>\d+)\s*gp\)\."
)

# Section terminator: the next subsection on page 70 is "Tools".
_SECTION_END_RE = re.compile(r"\bTools\b\s+A tool helps")


def _parse_pack_block(name: str, cost_gp: int, body: str) -> EquipmentPack:
    """Turn one pack's prose body into a structured pack dict."""
    # `body` starts with "Includes …" and ends just before the next pack
    # header (or the Tools section).
    body = body.strip().rstrip(".").rstrip()

    # Canonical description text: re-add the trailing period that we just
    # stripped so the assembled record is byte-equivalent to the retired
    # literal.
    description = f"{body}."

    # Split off the optional trailing sentence
    # ("The pack also has 50 feet of hempen rope strapped to the side of it.").
    trailing_re = re.compile(r"\.\s+The pack also has (?P<extra>.+?) strapped to the side of it")
    m = trailing_re.search(body)
    if m:
        contents_prose = body[: m.start()]  # everything up to ". The pack also has"
        extra_phrase = m.group("extra")
    else:
        contents_prose = body
        extra_phrase = None

    # Strip the leading "Includes " marker.
    if not contents_prose.startswith("Includes "):
        raise ValueError(
            f"{name}: pack prose does not start with 'Includes ': {contents_prose[:60]!r}"
        )
    contents_prose = contents_prose.removeprefix("Includes ")

    contents: list[PackContents] = []
    for token in _split_contents_tokens(contents_prose):
        contents.append(_resolve_token(name, token))

    if extra_phrase is not None:
        contents.append(_resolve_token(name, extra_phrase))

    return EquipmentPack(
        name=name,
        cost_gp=cost_gp,
        description=description,
        contents=contents,
        total_weight_lb=0.0,
        missing_items=[],
    )


def _split_contents_tokens(prose: str) -> list[str]:
    """Split a pack's `Includes …` body on commas, stripping the final 'and '."""
    # The SRD uses an Oxford comma so the final separator is also ", ".
    raw_tokens = [t.strip() for t in prose.split(", ")]
    # Strip leading "and " from any token (typically only the last one).
    cleaned = [t.removeprefix("and ").strip() for t in raw_tokens]
    return [t for t in cleaned if t]


def _resolve_token(pack_name: str, token: str) -> PackContents:
    """Map one '(qty,) phrase' token to a PackContents record."""
    # Try article prefix ("a backpack" / "an ink pen").
    article_match = re.match(r"^(?:a|an)\s+(.+)$", token)
    if article_match:
        parsed_qty = 1
        phrase = article_match.group(1)
    else:
        # Try leading digit ("10 pitons", "1,000 ball bearings", "2 days of rations").
        digit_match = re.match(r"^(\d+(?:,\d+)*)\s+(.+)$", token)
        if digit_match:
            parsed_qty = int(digit_match.group(1).replace(",", ""))
            phrase = digit_match.group(2)
        else:
            # No-article path ("sealing wax", "vestments").
            parsed_qty = 1
            phrase = token

    entry = _PHRASE_TO_ITEM.get(phrase)
    if entry is None:
        # Plural fallback: try stripping a trailing 's'.
        if phrase.endswith("s"):
            entry = _PHRASE_TO_ITEM.get(phrase[:-1])
        if entry is None:
            raise KeyError(
                f"{pack_name}: unmapped pack phrase {phrase!r} "
                f"(token={token!r}). Add it to _PHRASE_TO_ITEM."
            )

    item_id, item_name, qty_override = entry
    quantity = qty_override if qty_override is not None else parsed_qty
    return PackContents(item_id=item_id, item_name=item_name, quantity=quantity)


def extract_equipment_packs(pdf_path: Path) -> dict[str, Any]:
    """Extract the 7 SRD equipment packs from PDF page 70.

    Returns a dict matching the shape used by other dataset extractors:
        {"packs": [...], "_meta": {...}}
    """
    equipment_pages = PAGE_INDEX["equipment"]["pages"]
    if not (equipment_pages["start"] <= 70 <= equipment_pages["end"]):
        raise RuntimeError(
            "PAGE_INDEX['equipment'] no longer covers page 70 — "
            "extract_equipment_packs assumes the pack section is on page 70."
        )

    with open_pdf(pdf_path) as doc:
        text = page_text(doc, 69)  # PDF page 70 → 0-indexed doc[69]

    # Cap the search region at the start of the next subsection ("Tools").
    end_match = _SECTION_END_RE.search(text)
    if end_match:
        text = text[: end_match.start()]

    headers = list(_PACK_HEADER_RE.finditer(text))
    if not headers:
        raise RuntimeError(
            "No pack headers found on page 70. The reproducer "
            "test_equipment_packs_pdf_page_70_pack_header_extractable "
            "should have caught this earlier."
        )

    packs: list[EquipmentPack] = []
    for i, hdr in enumerate(headers):
        # SRD prose uses a curly apostrophe (U+2019); downstream JSON has
        # historically used the straight ASCII form. Normalize at the
        # extraction boundary so consumers don't have to.
        name = normalize_apostrophes(hdr.group("name"))
        cost_gp = int(hdr.group("cost"))
        body_start = hdr.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[body_start:body_end].strip()
        packs.append(_parse_pack_block(name, cost_gp, body))

    logger.info("Extracted %d equipment packs from PDF page 70", len(packs))

    return {
        "packs": packs,
        "_meta": {
            "extractor_version": EXTRACTOR_VERSION,
            "packs_extracted": len(packs),
            "pages_processed": [70],
        },
    }
