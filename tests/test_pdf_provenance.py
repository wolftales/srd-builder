"""Reproducer tests for provenance claims in docs/PROVENANCE.md.

Each test pins a specific assertion about what PDF extraction yields
*today* for a region we currently override with hand-curated data. The
tests are not regression guards — they are *truth probes*. When one
fails, our understanding of the source has shifted and the matching
manual override should be reassessed.

Tests skip gracefully when the source PDF is not present (CI / container
builds without the SRD bundle).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRD_5_1_PDF = REPO_ROOT / "rulesets" / "srd_5_1" / "SRD_CC_v5.1.pdf"


def _require_pdf_and_fitz():
    if not SRD_5_1_PDF.exists():
        pytest.skip(f"PDF not present at {SRD_5_1_PDF}")
    try:
        import fitz  # noqa: F401
    except ImportError:
        pytest.skip("pymupdf not installed")


def test_lineage_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 lineage pages ARE extractable, despite the claim in
    src/srd_builder/srd_5_1/lineage_targets.py that they are corrupted.

    The original "PDF text is corrupted" assertion (written years ago,
    likely against an older PyMuPDF) does not hold under pymupdf 1.27.x.
    The body text uses non-breaking spaces (U+00A0) and tab+CR sequences
    as word separators; once normalized via utils.pdf_probe, all lineage
    names and trait keywords are present.

    If this test starts FAILING (lineage names missing from a page),
    the PDF or PyMuPDF really has changed and a fresh investigation is
    needed. Either way, the manual LINEAGE_DATA override in
    lineage_targets.py is a strong candidate for retirement (see
    docs/PROVENANCE.md).
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        page_text,
        srd_page_to_pdf_index,
    )

    page_range = PAGE_INDEX["lineages"]["pages"]
    pdf_start = srd_page_to_pdf_index(page_range["start"])
    pdf_end = srd_page_to_pdf_index(page_range["end"])

    expected = {
        "Dwarf": 2,
        "Hill Dwarf": 3,
        "High Elf": 3,
        "Halfling": 4,
        "Lightfoot": 4,
        "Dragonborn": 4,
        "Gnome": 5,
        "Half-Elf": 5,
        "Half-Orc": 6,
        "Tiefling": 6,
    }

    for keyword, idx in expected.items():
        assert pdf_start <= idx <= pdf_end, (
            f"Test fixture out of sync with PAGE_INDEX: "
            f"{keyword!r} at PDF index {idx} not within "
            f"[{pdf_start}, {pdf_end}]"
        )

    missing: list[str] = []
    with open_pdf(SRD_5_1_PDF) as doc:
        for keyword, pdf_idx in expected.items():
            text = page_text(doc, pdf_idx)
            if keyword not in text:
                missing.append(f"{keyword!r} expected on PDF index {pdf_idx}")

    assert not missing, (
        "Lineage keywords no longer extractable from expected pages — "
        "investigate before changing LINEAGE_DATA assumptions:\n  - " + "\n  - ".join(missing)
    )


def test_spell_lists_pages_class_headers_are_extractable() -> None:
    """SRD 5.1 spell-list pages (105–113) ARE extractable, despite the
    claim in src/srd_builder/srd_5_1/spell_class_targets.py that the
    text is corrupted.

    spell_class_targets.py is the largest hand-curated surface in the
    project (~888 lines, 8 class spell lists, wired into every spell
    record via postprocess/spells.py). The "PDF text is corrupted;
    manually mapped via visual inspection" rationale is the same era
    and same author as the lineage claim that has already been disproved.

    This probe asserts that (a) all 8 class section headers and (b) a
    sampling of well-known spells appear in pages 105–113 after the
    standard whitespace normalization. If they do, SPELL_CLASSES is a
    retirement candidate; v0.27.0 should plan a real
    extract_spell_classes.py on top of utils.pdf_probe.
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        pages_text,
        srd_page_to_pdf_index,
    )

    page_range = PAGE_INDEX["spell_lists"]["pages"]
    pdf_start = srd_page_to_pdf_index(page_range["start"])
    pdf_end = srd_page_to_pdf_index(page_range["end"])
    pdf_indices = range(pdf_start, pdf_end + 1)

    expected_headers = [
        "Bard Spells",
        "Cleric Spells",
        "Druid Spells",
        "Paladin Spells",
        "Ranger Spells",
        "Sorcerer Spells",
        "Warlock Spells",
        "Wizard Spells",
    ]

    expected_spells = [
        "Vicious Mockery",
        "Sacred Flame",
        "Druidcraft",
        "Eldritch Blast",
        "Fire Bolt",
    ]

    with open_pdf(SRD_5_1_PDF) as doc:
        all_text = "\n".join(pages_text(doc, pdf_indices).values())

    missing_headers = [h for h in expected_headers if h not in all_text]
    missing_spells = [s for s in expected_spells if s not in all_text]

    assert not missing_headers, (
        "Spell-list class headers not found in pages "
        f"{page_range['start']}–{page_range['end']} after whitespace "
        "normalization:\n  - " + "\n  - ".join(missing_headers)
    )
    assert not missing_spells, (
        "Well-known spell names not found in pages "
        f"{page_range['start']}–{page_range['end']} after whitespace "
        "normalization (body text may genuinely be unreadable):\n  - "
        + "\n  - ".join(missing_spells)
    )


def test_class_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 class pages (8–55) ARE extractable, despite the claim in
    src/srd_builder/rulesets/srd_5_1/class_targets.py that the data was
    "manually transcribed via visual inspection."

    class_targets.py is the third-largest hand-curated surface in the
    project (~763 lines, all 12 classes with hit_die, proficiencies,
    feature lists, subclasses, and 20-level progression). Like
    lineage_targets.py (retired in v0.27.0 P1) and spell_class_targets.py
    (retired in v0.27.0 P2), the "manual transcription" rationale is
    the same era and same author as the lineage/spell-class claims
    already disproved.

    This probe asserts that (a) all 12 class names, (b) a sampling of
    well-known features, and (c) common section headers appear in
    pages 8–55 after the standard whitespace normalization. If they
    do, CLASS_DATA is a retirement candidate; a future release should
    plan a real extract_classes.py on top of utils.pdf_probe + the
    font-fingerprint walk pattern used by extract_lineages.py and
    extract_spell_classes.py. The full structural payload (proficiencies
    dict, feature IDs, level progression) is significantly richer than
    a flat spell list, so a retirement will need a larger extractor —
    the point of this probe is only to confirm the *text* is present.
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        pages_text,
        srd_page_to_pdf_index,
    )

    page_range = PAGE_INDEX["classes"]["pages"]
    pdf_start = srd_page_to_pdf_index(page_range["start"])
    pdf_end = srd_page_to_pdf_index(page_range["end"])
    pdf_indices = range(pdf_start, pdf_end + 1)

    expected_class_names = [
        "Barbarian",
        "Bard",
        "Cleric",
        "Druid",
        "Fighter",
        "Monk",
        "Paladin",
        "Ranger",
        "Rogue",
        "Sorcerer",
        "Warlock",
        "Wizard",
    ]
    expected_features = [
        "Rage",
        "Unarmored Defense",
        "Spellcasting",
        "Sneak Attack",
        "Action Surge",
        "Wild Shape",
        "Lay on Hands",
        "Divine Sense",
        "Favored Enemy",
        "Cunning Action",
        "Sorcerous Origin",
        "Pact Magic",
        "Arcane Recovery",
        "Bardic Inspiration",
        "Channel Divinity",
    ]
    expected_sections = [
        "Hit Points",
        "Proficiencies",
        "Equipment",
        "Primal Path",
        "Bard College",
        "Divine Domain",
    ]

    with open_pdf(SRD_5_1_PDF) as doc:
        all_text = "\n".join(pages_text(doc, pdf_indices).values())

    missing_classes = [c for c in expected_class_names if c not in all_text]
    missing_features = [f for f in expected_features if f not in all_text]
    missing_sections = [s for s in expected_sections if s not in all_text]

    assert not missing_classes, (
        f"Class names not found in pages {page_range['start']}–"
        f"{page_range['end']} after whitespace normalization:\n  - "
        + "\n  - ".join(missing_classes)
    )
    assert not missing_features, (
        f"Well-known class features not found in pages {page_range['start']}–"
        f"{page_range['end']} after whitespace normalization "
        "(body text may genuinely be unreadable):\n  - " + "\n  - ".join(missing_features)
    )
    assert not missing_sections, (
        f"Class section headers not found in pages {page_range['start']}–"
        f"{page_range['end']} after whitespace normalization:\n  - "
        + "\n  - ".join(missing_sections)
    )


def test_poison_pages_are_extractable_after_whitespace_normalization() -> None:
    """SRD 5.1 poison pages (204–205) ARE extractable, despite the
    "corrupted text on pages 204-205" claim in
    src/srd_builder/rulesets/srd_5_1/poison_descriptions.py.

    Fourth hand-curated "PDF corruption" claim in the codebase, fourth
    one to fail under reproducer scrutiny. Same era, same author as
    lineage_targets (retired v0.27.0 P1), spell_class_targets
    (retired v0.27.0 P2), and class_targets (DISPUTED v0.27.0 P3).

    This probe asserts that (a) all 14 SRD poison names, (b) the
    standard mechanic keywords (DC numbers, "Constitution saving
    throw", duration phrases), and (c) the opening section title
    "Poisons" appear in pages 204–205 after the standard whitespace
    normalization. They do — every one.

    **Status (v0.27.2):** The upstream splitter bugs that originally
    blocked retirement have been fixed in
    ``utils.postprocess.text.clean_text`` (smart-quote normalization
    was a source-mangled no-op) and ``utils.prose.split_by_known_headers``
    (now accepts a ``start_marker`` so the splitter skips the price-table
    preamble at the top of page 204). See
    ``test_poison_descriptions_extract_all_14_sections_cleanly`` for the
    end-to-end assertion. The hand-curated POISON_DESCRIPTIONS map is
    still retained as the source of truth for poison damage formulas
    until the parser learns the "taking X poison damage on a failed
    save" pattern.
    """
    _require_pdf_and_fitz()
    from srd_builder.utils.pdf_probe import (
        open_pdf,
        pages_text,
        srd_page_to_pdf_index,
    )

    pdf_start = srd_page_to_pdf_index(204)
    pdf_end = srd_page_to_pdf_index(205)
    pdf_indices = range(pdf_start, pdf_end + 1)

    expected_poison_names = [
        "Assassin",  # 'Assassin's Blood' — fancy apostrophe in PDF
        "Burnt Othur Fumes",
        "Crawler Mucus",
        "Drow Poison",
        "Essence of Ether",
        "Malice",
        "Midnight Tears",
        "Oil of Taggit",
        "Pale Tincture",
        "Purple Worm Poison",
        "Serpent Venom",
        "Torpor",
        "Truth Serum",
        "Wyvern Poison",
    ]
    expected_mechanics = [
        "DC 10",
        "DC 13",
        "DC 15",
        "DC 17",
        "DC 19",
        "Constitution saving throw",
        "poison damage",
        "1 minute",
        "1 hour",
        "24 hours",
    ]
    expected_sections = ["Poisons"]

    with open_pdf(SRD_5_1_PDF) as doc:
        all_text = "\n".join(pages_text(doc, pdf_indices).values())

    missing_poisons = [p for p in expected_poison_names if p not in all_text]
    missing_mechanics = [m for m in expected_mechanics if m not in all_text]
    missing_sections = [s for s in expected_sections if s not in all_text]

    assert not missing_poisons, (
        "Poison names not found in pages 204–205 after whitespace "
        "normalization:\n  - " + "\n  - ".join(missing_poisons)
    )
    assert not missing_mechanics, (
        "Poison mechanics keywords not found in pages 204–205 after "
        "whitespace normalization (body text may genuinely be "
        "unreadable):\n  - " + "\n  - ".join(missing_mechanics)
    )
    assert not missing_sections, (
        "Poison section header not found in pages 204–205 after "
        "whitespace normalization:\n  - " + "\n  - ".join(missing_sections)
    )


def test_poison_descriptions_extract_all_14_sections_cleanly() -> None:
    """End-to-end regression for the v0.27.2 splitter + clean_text fix.

    Before the fix:
      * the splitter dropped "Assassin's Blood" entirely (excluded from
        known_headers because the smart-quote no-op in clean_text made
        the regex unmatchable);
      * "Malice" locked onto its price-table row at the top of page 204
        and absorbed ~2000 chars from neighbouring sections;
      * "Torpor" did the same and absorbed ~3700 chars.

    After the fix (``utils.postprocess.text.clean_text`` normalizes
    U+2018/U+2019/U+201C/U+201D, and ``utils.prose.split_by_known_headers``
    accepts a ``start_marker`` set to "Sample Poisons" in the
    ``poison_descriptions`` config) the live extractor returns all 14
    sections at description-shaped lengths.
    """
    _require_pdf_and_fitz()
    from srd_builder.assemble.assemble_prose import assemble_prose_dataset
    from srd_builder.parse.parse_poison_descriptions import (
        parse_poison_description_records,
    )

    doc = assemble_prose_dataset(
        "poison_descriptions",
        SRD_5_1_PDF,
        parse_poison_description_records,
        "srd_5_1",
    )
    items = doc.get("poison_descriptions", doc.get("items", []))

    expected_simple_names = {
        "assassins_blood",
        "burnt_othur_fumes",
        "crawler_mucus",
        "drow_poison",
        "essence_of_ether",
        "malice",
        "midnight_tears",
        "oil_of_taggit",
        "pale_tincture",
        "purple_worm_poison",
        "serpent_venom",
        "torpor",
        "truth_serum",
        "wyvern_poison",
    }
    got = {p["simple_name"] for p in items}
    missing = expected_simple_names - got
    extra = got - expected_simple_names
    assert not missing, f"Poison descriptions missing from live extractor: {sorted(missing)}"
    assert not extra, f"Unexpected poison descriptions from live extractor: {sorted(extra)}"

    # Description length sanity: real poison descriptions in the SRD run
    # 150–500 chars. Anything above 800 means a section absorbed the next
    # one (the pre-fix malice/torpor regression).
    over_long = [
        (p["simple_name"], len(p.get("description") or ""))
        for p in items
        if len(p.get("description") or "") > 800
    ]
    assert not over_long, (
        "Poison descriptions absorbed neighbouring sections "
        "(>800 chars):\n  " + "\n  ".join(f"{n}: {ln} chars" for n, ln in over_long)
    )

    # Every section must have a Constitution save DC parsed out — that
    # is the single uniform mechanic across all 14 SRD poisons.
    missing_save = [p["simple_name"] for p in items if not (p.get("save") or {}).get("dc")]
    assert not missing_save, "Poison descriptions missing parsed save DC:\n  - " + "\n  - ".join(
        missing_save
    )

    assert doc.get("_meta", {}).get("warnings", []) == [], (
        f"Poison description extractor produced warnings: {doc['_meta']['warnings']}"
    )


def test_class_progression_truncations_are_real() -> None:
    """The class progression tables on pages 8, 35, 39, and 54 of the
    SRD 5.1 PDF have specific cells whose text is genuinely not
    extractable via any PyMuPDF API. This test pins those truncations
    so the manual entries in
    ``src/srd_builder/extract/datasets/extract_classes._PROGRESSION_FIXES``
    stay reproducer-backed.

    If any of these ``search_for`` calls starts returning a hit at the
    expected y-coordinate, the matching ``_PROGRESSION_FIXES`` entry
    can be retired.
    """
    _require_pdf_and_fitz()
    import fitz

    doc = fitz.open(str(SRD_5_1_PDF))
    try:
        # Barbarian L11 cell at pi=7 shows "Relentless" but the second
        # line "Rage" is absent. ``search_for("Relentless Rage")``
        # returns zero hits anywhere on the page.
        assert len(doc[7].search_for("Relentless Rage")) == 0, (
            "Barbarian L11 'Relentless Rage' became extractable — "
            "_PROGRESSION_FIXES['barbarian'][11] override can be dropped."
        )

        # Ranger L8 cell at pi=34: "Land's Stride" — only the first
        # word "Land" extracts; the curly-apostrophe + " Stride" tail
        # never appears in any span at the L8 row y (~400-415).
        ranger = doc[34]
        lands_stride_hits = ranger.search_for("Land's Stride")
        row_band = [h for h in lands_stride_hits if 395 < h.y0 < 420]
        assert not row_band, (
            "Ranger L8 'Land's Stride' became extractable in the row — "
            "_PROGRESSION_FIXES['ranger'][8] override can be dropped."
        )

        # Rogue L10 cell at pi=38: "Improvement" never surfaces at
        # y>688 (the L10 row sits at y≈688; "Improvement" appears
        # elsewhere on the page but not in that cell).
        rogue = doc[38]
        improv_in_l10 = [h for h in rogue.search_for("Improvement") if h.y0 > 688]
        assert not improv_in_l10, (
            "Rogue L10 'Improvement' became extractable — "
            "_PROGRESSION_FIXES['rogue'][10] override can be dropped."
        )

        # Wizard L20 cell at pi=52: "Signature Spells" — the trailing
        # "s" is missing from the L20 cell; "Signature Spell"
        # (singular) extracts. The full plural phrase has zero hits in
        # the table area (y < 500).
        wizard = doc[52]
        sig_spells_plural = wizard.search_for("Signature Spells")
        table_band = [h for h in sig_spells_plural if h.y0 < 500]
        assert not table_band, (
            "Wizard L20 'Signature Spells' became extractable in the "
            "table row — _PROGRESSION_FIXES['wizard'][20] override can be dropped."
        )
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Audit: extractor page constants agree with utils.page_index.PAGE_INDEX
# ---------------------------------------------------------------------------
#
# Historically each per-dataset extractor hardcoded its own (start, end) PDF
# page constants, with no cross-check against the canonical PAGE_INDEX table.
# In v0.27.4 this surfaced a real data-loss bug: extract_equipment.py was
# 0-indexed where the other three were 1-indexed, and its end constant was
# off by one — silently dropping PDF page 74 (Services / Lifestyle /
# Spellcasting Services tables) on every build.
#
# This test pins all four extractors (equipment, spells, magic_items,
# conditions) against PAGE_INDEX so the next drift fails CI instead of
# disappearing into hand-curated workaround data.


@pytest.mark.parametrize(
    ("module_path", "start_attr", "end_attr", "page_index_key"),
    [
        (
            "srd_builder.extract.datasets.extract_equipment",
            "EQUIPMENT_START_PAGE",
            "EQUIPMENT_END_PAGE",
            "equipment",
        ),
        (
            "srd_builder.extract.datasets.extract_spells",
            "SPELL_START_PAGE",
            "SPELL_END_PAGE",
            "spell_descriptions",
        ),
        (
            "srd_builder.extract.datasets.extract_magic_items",
            "MAGIC_ITEMS_START_PAGE",
            "MAGIC_ITEMS_END_PAGE",
            "magic_items",
        ),
        (
            "srd_builder.extract.datasets.extract_conditions",
            "CONDITION_START_PAGE",
            "CONDITION_END_PAGE",
            "appendix_ph_a_conditions",
        ),
    ],
)
def test_extractor_page_constants_agree_with_page_index(
    module_path: str,
    start_attr: str,
    end_attr: str,
    page_index_key: str,
) -> None:
    """Each extractor's (START, END) constants must match PAGE_INDEX[key].

    All four extractors use the 1-indexed PDF page convention. If a constant
    drifts (e.g. someone re-introduces the 0-indexed mistake or trims a page
    by accident), this test fails before the bug ships.
    """
    import importlib

    from srd_builder.utils.page_index import PAGE_INDEX

    module = importlib.import_module(module_path)
    start = getattr(module, start_attr)
    end = getattr(module, end_attr)
    expected = PAGE_INDEX[page_index_key]["pages"]

    assert start == expected["start"], (
        f"{module_path}.{start_attr} = {start} "
        f"but PAGE_INDEX[{page_index_key!r}].start = {expected['start']}"
    )
    assert end == expected["end"], (
        f"{module_path}.{end_attr} = {end} "
        f"but PAGE_INDEX[{page_index_key!r}].end = {expected['end']}"
    )


# ---------------------------------------------------------------------------
# Reproducer: equipment_packs.py — is PDF page 70 extractable?
# ---------------------------------------------------------------------------
#
# src/srd_builder/assemble/equipment_packs.py (323 lines) hand-transcribes
# all 7 SRD equipment packs (Burglar's, Diplomat's, Dungeoneer's,
# Entertainer's, Explorer's, Priest's, Scholar's) with item-by-item
# contents lists. The module header claims "Extracted from SRD 5.1
# page 70" but no extractor exists; the data is a Python literal.
#
# Per AGENTS.md § "PDF extraction discipline (no magic wands)", we must
# write a reproducer that proves the region is or is not extractable
# before declaring the hand-curated module necessary.
#
# Result: page 70 yields all 7 pack headers + costs + comma-separated
# contents prose under standard whitespace normalization. The pack
# section is fully parseable — no PDF corruption.


# Expected packs as they appear in the SRD prose on page 70.
# Note the curly apostrophe (U+2019), not a straight ASCII apostrophe.
_EXPECTED_PACKS: list[tuple[str, int]] = [
    ("Burglar\u2019s Pack", 16),
    ("Diplomat\u2019s Pack", 39),
    ("Dungeoneer\u2019s Pack", 12),
    ("Entertainer\u2019s Pack", 40),
    ("Explorer\u2019s Pack", 10),
    ("Priest\u2019s Pack", 19),
    ("Scholar\u2019s Pack", 40),
]


def _load_page_70_text() -> str:
    """Return whitespace-normalized text of SRD PDF page 70."""
    from srd_builder.utils.page_index import PAGE_INDEX
    from srd_builder.utils.pdf_probe import open_pdf, page_text

    equipment_pages = PAGE_INDEX["equipment"]["pages"]
    assert equipment_pages["start"] <= 70 <= equipment_pages["end"], (
        "PAGE_INDEX['equipment'] no longer covers page 70 — update this test."
    )

    with open_pdf(SRD_5_1_PDF) as doc:
        return page_text(doc, 69)  # 0-indexed: PDF page 70 → doc[69]


def test_equipment_packs_pdf_page_70_section_header_extractable() -> None:
    """The 'Equipment Packs' section header on PDF page 70 must be extractable.

    This is the cheapest possible probe — if the section header itself is
    missing, the page is in trouble and no parser can recover the data.
    """
    _require_pdf_and_fitz()
    text = _load_page_70_text()
    assert "Equipment Packs" in text, (
        "'Equipment Packs' section header not found in page 70 text — "
        "extraction is broken at the section level."
    )


@pytest.mark.parametrize(("pack_name", "cost_gp"), _EXPECTED_PACKS)
def test_equipment_packs_pdf_page_70_pack_header_extractable(
    pack_name: str,
    cost_gp: int,
) -> None:
    """Each of the 7 SRD packs has its '{Name} ({cost} gp).' header on page 70.

    This is the parser anchor: a regex like
    r"(\\w+\u2019s Pack) \\((\\d+) gp\\)\\. Includes (.+?)(?=\\.\\s+\\w+\u2019s Pack|\\.\\s+Tools)"
    can split the section into 7 (name, cost, contents-prose) tuples.
    """
    _require_pdf_and_fitz()
    text = _load_page_70_text()
    header = f"{pack_name} ({cost_gp} gp)."
    assert header in text, (
        f"Pack header {header!r} not found in page 70 text. The hand-curated "
        f"{pack_name!r} entry in equipment_packs.py cannot be justified by "
        f"'PDF corruption'; the parser just needs to be written."
    )


@pytest.mark.parametrize(
    ("pack_name", "signature_items"),
    [
        # One distinctive multi-word phrase per pack, picked from the SRD
        # contents list. If these phrases survive extraction, the full
        # comma-separated contents list survives — a parser can split on
        # ", " and recognize quantities like "10 pitons" / "2 flasks of oil".
        ("Burglar\u2019s Pack", ["bag of 1,000 ball bearings", "10 pitons"]),
        ("Diplomat\u2019s Pack", ["2 cases for maps and scrolls", "set of fine clothes"]),
        ("Dungeoneer\u2019s Pack", ["10 torches", "10 days of rations"]),
        ("Entertainer\u2019s Pack", ["2 costumes", "disguise kit"]),
        ("Explorer\u2019s Pack", ["mess kit", "50 feet of hempen rope"]),
        ("Priest\u2019s Pack", ["2 blocks of incense", "vestments"]),
        ("Scholar\u2019s Pack", ["book of lore", "10 sheets of parchment"]),
    ],
)
def test_equipment_packs_pdf_page_70_contents_extractable(
    pack_name: str,
    signature_items: list[str],
) -> None:
    """Each pack's distinctive contents phrases survive extraction on page 70.

    The SRD lists pack contents as comma-separated prose immediately after
    the '{Name} ({cost} gp). Includes ' header. If these signature phrases
    survive whitespace normalization, the full contents list does too, and
    a parser can split on ', ' / 'and ' to enumerate items with quantities.
    """
    _require_pdf_and_fitz()
    text = _load_page_70_text()
    # Anchor on the header so we know we're inside the right pack's prose.
    pack_idx = text.find(pack_name)
    assert pack_idx >= 0, (
        f"Pack header {pack_name!r} missing — earlier test should have caught this."
    )
    # The pack's contents extend to the next pack header (or the 'Tools'
    # section heading at the bottom of page 70).
    after = text[pack_idx:]
    for phrase in signature_items:
        assert phrase in after, (
            f"Signature phrase {phrase!r} not found inside the {pack_name} "
            f"contents prose on page 70. If this fails, the parser-design "
            f"assumption (comma-separated SRD prose) needs revisiting."
        )


# ---------------------------------------------------------------------------
# equipment_descriptions.py reproducer (v0.27.5 — pre-P7 cutover)
# ---------------------------------------------------------------------------
# Mirrors the structure of the equipment_packs reproducer above. This batch
# proves that the prose descriptions which currently live as four hand-
# curated Python literals
# (`ADVENTURE_GEAR_DESCRIPTIONS`, `TOOLS_DESCRIPTIONS`, `ARMOR_DESCRIPTIONS`,
# `LIFESTYLE_DESCRIPTIONS`, ~398 lines total in
# `src/srd_builder/assemble/equipment_descriptions.py`) are in fact
# extractable from their respective PDF pages (63, 66–68, 71, 73) under the
# same whitespace normalization used by every other v0.27.x extractor.
#
# Why a reproducer comes first: the same "PDF text is corrupted / missing"
# rationale has now been disproven five times in a row (lineages, spell-
# classes, classes, poisons, equipment_packs). Before writing the parser
# for P7, AGENTS.md § "PDF extraction discipline" requires evidence that
# the section is recoverable.
#
# Result: every section anchor is present on its expected PDF page, and
# every probed item heading is followed (within ~600 chars) by a
# distinctive content phrase from its SRD description. The parser just
# needs to be written.


def _page_text_normalized(pdf_page_1_indexed: int) -> str:
    """Return whitespace-normalized text of the given 1-indexed SRD PDF page."""
    from srd_builder.utils.pdf_probe import open_pdf, page_text

    with open_pdf(SRD_5_1_PDF) as doc:
        return page_text(doc, pdf_page_1_indexed - 1)


# Section anchors: the first heading the parser would land on in each
# section. If any of these are missing, the section is in trouble at the
# structural level and no item-by-item probe will help.
_EQUIPMENT_DESCRIPTION_SECTION_ANCHORS: list[tuple[str, int, str]] = [
    # (section_label, pdf_page_1_indexed, heading_with_trailing_period)
    ("adventuring_gear", 66, "Acid."),
    ("tools", 71, "Disguise Kit."),
    ("armor", 63, "Padded."),
    ("lifestyle", 73, "Wretched."),
]


@pytest.mark.parametrize(
    ("section_label", "pdf_page", "anchor_heading"),
    _EQUIPMENT_DESCRIPTION_SECTION_ANCHORS,
)
def test_equipment_descriptions_section_anchor_extractable(
    section_label: str,
    pdf_page: int,
    anchor_heading: str,
) -> None:
    """The first prose-description heading of each section must be present.

    Cheapest possible probe per section: if the section's first heading
    is missing from the expected PDF page, the page is broken at the
    structural level and the hand-curated module's `pdf_missing`
    rationale would (this once) be justified. Every other v0.27.x
    reproducer in this file has shown the opposite is the case.
    """
    _require_pdf_and_fitz()
    text = _page_text_normalized(pdf_page)
    assert anchor_heading in text, (
        f"Section anchor {anchor_heading!r} ({section_label}) not found on "
        f"PDF page {pdf_page}. If this fails, the hand-curated "
        f"equipment_descriptions.py *_DESCRIPTIONS list is the only source "
        f"for that section's prose."
    )


# Per-item signature probes: (section_label, pdf_page, heading, signature_phrase).
# Each heading is the bold item label as it appears in SRD prose, and the
# signature phrase is a distinctive piece of that item's description that
# survives standard whitespace normalization (no soft-hyphen artifacts
# inside compound words). The probe asserts the signature appears within
# 600 chars after the heading start on the expected page — strong evidence
# that a parser anchored on `^[A-Z][A-Za-z ’,()]+\.\s` can lift the prose.
_EQUIPMENT_DESCRIPTION_ITEM_PROBES: list[tuple[str, int, str, str]] = [
    # adventure gear — pp. 66–68
    ("adventuring_gear", 66, "Acid.", "splash the contents of this vial"),
    ("adventuring_gear", 66, "Antitoxin.", "saving throws against poison for 1 hour"),
    ("adventuring_gear", 67, "Ball Bearings.", "spill these tiny metal balls"),
    ("adventuring_gear", 67, "Caltrops.", "stop moving this turn"),
    ("adventuring_gear", 68, "Manacles.", "DC 20 Dexterity check"),
    ("adventuring_gear", 68, "Spyglass.", "twice their size"),
    # tools — p. 71
    ("tools", 71, "Disguise Kit.", "pouch of cosmetics, hair dye"),
    ("tools", 71, "Forgery Kit.", "small box contains a variety"),
    ("tools", 71, "Poisoner", "vials, chemicals, and other equipment"),
    # armor — p. 63 (note: PDF text flows the prose without "Padded armor"
    # repeating the heading word, so signature phrases are domain text)
    ("armor", 63, "Padded.", "quilted layers of cloth and batting"),
    ("armor", 63, "Ring mail", "inferior to chain mail"),
    # lifestyle — p. 73 (cost table appears before the prose headings, so
    # we explicitly anchor on the `Wretched.` prose heading, not just the
    # word `Wretched` which appears earlier in the cost table)
    ("lifestyle", 73, "Wretched.", "inhumane conditions"),
    ("lifestyle", 73, "Aristocratic.", "life of plenty and comfort"),
]


@pytest.mark.parametrize(
    ("section_label", "pdf_page", "heading", "signature_phrase"),
    _EQUIPMENT_DESCRIPTION_ITEM_PROBES,
)
def test_equipment_descriptions_item_signature_extractable(
    section_label: str,
    pdf_page: int,
    heading: str,
    signature_phrase: str,
) -> None:
    """Each probed item's heading + signature phrase survive extraction.

    A `find()` on the heading anchors the probe inside the right item's
    paragraph; the signature phrase is then required to appear within
    the next 600 chars. This is the same shape as the equipment-packs
    contents reproducer above and proves a parser can lift the prose
    body for each item by walking from one heading to the next.
    """
    _require_pdf_and_fitz()
    text = _page_text_normalized(pdf_page)
    heading_idx = text.find(heading)
    assert heading_idx >= 0, (
        f"Heading {heading!r} ({section_label}) not found on PDF page "
        f"{pdf_page} — section anchor test should have caught structural "
        f"breakage first."
    )
    body = text[heading_idx : heading_idx + 600]
    assert signature_phrase in body, (
        f"Signature phrase {signature_phrase!r} not found within 600 chars "
        f"after heading {heading!r} on PDF page {pdf_page}. The "
        f"hand-curated {section_label} description for this item cannot "
        f"be justified by 'PDF corruption'; the parser just needs to be "
        f"written."
    )
