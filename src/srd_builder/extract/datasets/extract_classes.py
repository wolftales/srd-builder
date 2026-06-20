"""Extract class structures from SRD 5.1 PDF pages 8-55.

Replaces the hand-curated ``rulesets/srd_5_1/class_targets.py`` (~763
lines, in service since v0.8.2). The "manually transcribed via visual
inspection" rationale on that file was disproven by
[tests/test_pdf_provenance.py::test_class_pages_are_extractable_after_whitespace_normalization](../../../tests/test_pdf_provenance.py)
in v0.27.0 (DISPUTED).

Font fingerprints on pages 8-55 (verified 2026-06-18 against
SRD_CC_v5.1.pdf via PyMuPDF 1.27.x):

- 25.9pt GillSans-SemiBold       — class name (12 hits across the range:
                                   Barbarian, Bard, ..., Wizard)
- 18.0pt GillSans-SemiBold       — "Class Features" subheader (skip)
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

1. (landed) class discovery: ``name``, ``simple_name``, ``page``
2. (landed) ``hit_die``, ``primary_abilities``,
   ``saving_throw_proficiencies``, ``proficiencies``
3. (landed) ``features`` + ``subclasses``
4. (landed) ``spellcasting`` block (8 caster classes)
5. (this commit) ``progression`` (bbox-aware Features column walk over
   the per-class first-page tables, with a small ``_PROGRESSION_FIXES``
   map for cells the SRD PDF genuinely fails to expose — verified via
   ``page.search_for()`` reproducer; see
   [tests/test_pdf_provenance.py](../../../tests/test_pdf_provenance.py))
6. cutover ``parse_classes`` / ``parse_features``, delete
   ``class_targets.py``, retire from PROVENANCE
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

from srd_builder.postprocess.ids import normalize_id
from srd_builder.utils.pdf_layout import cluster_values_by_gap, iter_page_spans
from srd_builder.utils.pdf_probe import normalize_whitespace
from srd_builder.utils.prose import clean_text

CLASS_PAGES_PDF_INDICES = range(7, 55)  # SRD pages 8-55 (PDF idx 7-54)

_CLASS_NAME_SIZE = 25.9
_FONT_PREFIX = "GillSans"

# Field labels that live inside the "Proficiencies"/"Hit Points" boxes
# at the top of each class's first page. The body content sits in
# 9.8pt Cambria spans that follow the matching 9.8pt Cambria-Bold span,
# and runs until the next label or any 12pt+ GillSans heading.
_FIELD_LABEL_RE = re.compile(
    r"^(Hit Dice|Hit Points at \w+ Level\w*|Armor|Weapons|Tools|Saving Throws|Skills):$"
)
_HIT_DIE_RE = re.compile(r"\d+d(\d+)\b")

# Word-to-int for "Choose two from ...".
_NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4}

# Ability names appear capitalized in the "Saving Throws:" line; legacy
# CLASS_DATA stores them lowercase.
_ABILITY_NAMES_LOWER = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "wisdom",
    "charisma",
)

# SRD 5.1 does NOT print "Primary Ability:" in the class body — it
# appears only in the 5e PHB, not in the SRD. Verified 2026-06-18 by
# grepping pages 8, 24, 26 for /[Pp]rimary/ — zero matches. The legacy
# CLASS_DATA value is inferred curation. This lookup preserves the
# legacy field with a 12-line constant instead of 763.
_PRIMARY_ABILITIES: dict[str, list[str]] = {
    "barbarian": ["strength"],
    "bard": ["charisma"],
    "cleric": ["wisdom"],
    "druid": ["wisdom"],
    "fighter": ["strength", "dexterity"],
    "monk": ["dexterity", "wisdom"],
    "paladin": ["strength", "charisma"],
    "ranger": ["dexterity", "wisdom"],
    "rogue": ["dexterity"],
    "sorcerer": ["charisma"],
    "warlock": ["charisma"],
    "wizard": ["intelligence"],
}


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
                    "hit_die": "d12",
                    "primary_abilities": ["strength"],
                    "saving_throw_proficiencies": ["strength", "constitution"],
                    "proficiencies": {
                        "armor": ["light", "medium", "shields"],
                        "weapons": ["simple", "martial"],
                        "tools": [],
                        "skills": {"choose": 2, "from": [...]},
                    },
                    "features": ["feature:rage", "feature:unarmored_defense", ...],
                    "subclasses": ["subclass:path_of_the_berserker"],
                    # 8 caster classes also carry:
                    # "spellcasting": {"ability": "Wis", "spell_list": "cleric"}
                    # (later commits add progression)
                },
                ...
            ],
        }
    """
    pdf_path = Path(pdf_path)

    with fitz.open(str(pdf_path)) as doc:
        # Phase 1: locate the 25.9pt class-name span on each class's
        # first page so we know each class's page range.
        page_spans: dict[int, list[tuple[str, float, str, tuple]]] = {
            pi: _collect_spans(doc[pi]) for pi in CLASS_PAGES_PDF_INDICES
        }
        starts: list[tuple[int, str]] = []
        for pi, spans in page_spans.items():
            for txt, sz, font, _ in spans:
                if sz == _CLASS_NAME_SIZE and _FONT_PREFIX in font and txt:
                    starts.append((pi, txt))
                    break

        # Phase 2: for each class, derive its page range as
        # [start_pi, next_start_pi) (or end-of-classes for the last one)
        # and pull all field groups from those pages.
        classes: list[dict[str, Any]] = []
        for idx, (pi, name) in enumerate(starts):
            next_pi = starts[idx + 1][0] if idx + 1 < len(starts) else CLASS_PAGES_PDF_INDICES.stop
            class_spans: list[tuple[str, float, str, tuple]] = []
            for p in range(pi, next_pi):
                class_spans.extend(page_spans[p])
            # Progression tables live exclusively on the class's first
            # page (verified empirically — non-first class pages emit
            # zero 8.9pt Calibri spans except for paladin's "Oath
            # Spells" sidebar and stray body-paragraph fall-throughs).
            first_page_spans = page_spans[pi]
            classes.append(_build_class_record(name, pi, class_spans, first_page_spans))

    return {"source_pages": "8-55", "classes": classes}


def _build_class_record(
    name: str,
    pi: int,
    class_spans: list[tuple[str, float, str, tuple]],
    first_page_spans: list[tuple[str, float, str, tuple]],
) -> dict[str, Any]:
    """Assemble a single class record from its accumulated page spans."""
    simple = normalize_id(name)
    record: dict[str, Any] = {
        "name": name,
        "simple_name": simple,
        "page": pi + 1,
        "primary_abilities": _PRIMARY_ABILITIES[simple],
    }
    record.update(_extract_field_labels(class_spans))
    features, subclasses = _extract_features_and_subclasses(class_spans, simple)
    record["features"] = features
    record["subclasses"] = subclasses
    spellcasting = _extract_spellcasting(class_spans, simple)
    if spellcasting is not None:
        record["spellcasting"] = spellcasting
    record["progression"] = _extract_progression(first_page_spans, simple)
    return record


def _collect_spans(page: fitz.Page) -> list[tuple[str, float, str, tuple]]:
    """Flatten the page into ``(text, size, font, bbox)`` tuples in order.

    Delegates the block/line/span walk to ``iter_page_spans``; this
    module's only added work is the per-span ``normalize_whitespace``
    pass + empty-text filter + tuple shape that the rest of
    ``extract_classes`` already consumes.
    """
    return [
        (txt, round(span.get("size", 0), 1), span.get("font", ""), span["bbox"])
        for span in iter_page_spans(page.get_text("dict"))
        if (txt := normalize_whitespace(span["text"]))
    ]


def _extract_field_labels(
    spans: list[tuple[str, float, str, tuple]],
) -> dict[str, Any]:
    """Walk spans, capturing each ``<Label>:`` block's body text.

    Body runs until the next label or any 12pt+ GillSans heading.
    """
    bodies: dict[str, str] = {}
    i = 0
    while i < len(spans):
        txt, sz, font, _ = spans[i]
        m = _FIELD_LABEL_RE.match(txt) if sz == 9.8 and font == "Cambria-Bold" else None
        if m is None:
            i += 1
            continue
        label = m.group(1)
        body_parts: list[str] = []
        j = i + 1
        while j < len(spans):
            tj, szj, fj, _ = spans[j]
            if szj == 9.8 and fj == "Cambria-Bold" and _FIELD_LABEL_RE.match(tj):
                break
            if szj >= 12.0 and "GillSans" in fj:
                break
            if szj == 9.8 and "Cambria" in fj:
                body_parts.append(tj)
            j += 1
        bodies[label] = clean_text(" ".join(body_parts))
        i = j

    out: dict[str, Any] = {}
    if "Hit Dice" in bodies:
        out["hit_die"] = _parse_hit_die(bodies["Hit Dice"])
    if "Saving Throws" in bodies:
        out["saving_throw_proficiencies"] = _parse_saving_throws(bodies["Saving Throws"])
    out["proficiencies"] = {
        "armor": _parse_armor(bodies.get("Armor", "")),
        "weapons": _parse_weapons(bodies.get("Weapons", "")),
        "tools": _parse_tools(bodies.get("Tools", "")),
        "skills": _parse_skills(bodies.get("Skills", "")),
    }
    return out


def _parse_hit_die(text: str) -> str:
    """``"1d12 per barbarian level"`` → ``"d12"``."""
    m = _HIT_DIE_RE.search(text)
    return f"d{m.group(1)}" if m else ""


def _parse_saving_throws(text: str) -> list[str]:
    """``"Strength, Constitution"`` → ``["strength", "constitution"]``."""
    return [
        part.strip().lower()
        for part in text.split(",")
        if part.strip().lower() in _ABILITY_NAMES_LOWER
    ]


def _parse_armor(text: str) -> list[str]:
    """``"Light armor, medium armor, shields"`` → ``["light", "medium", "shields"]``.

    ``"None"`` → ``[]``. ``"All armor, shields"`` → ``["all", "shields"]``.
    Parenthetical clarifiers (druid's "...made of metal") are dropped.
    """
    text = re.sub(r"\s*\([^)]*\)", "", text).strip()
    if text.lower() in {"none", ""}:
        return []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        low = p.lower()
        if low.endswith(" armor"):
            low = low[: -len(" armor")]
        out.append(low)
    return out


def _parse_weapons(text: str) -> list[str]:
    """``"Simple weapons, martial weapons"`` → ``["simple", "martial"]``.

    ``"Daggers, darts, ..."`` → ``["daggers", "darts", ...]``.
    """
    if not text or text.lower() == "none":
        return []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    out: list[str] = []
    for p in parts:
        low = p.lower()
        if low.endswith(" weapons"):
            low = low[: -len(" weapons")]
        elif low.endswith(" weapon"):
            low = low[: -len(" weapon")]
        out.append(low)
    return out


def _parse_tools(text: str) -> list[str]:
    """``"None"`` → ``[]``; anything else becomes a single lowercase entry."""
    if not text or text.lower() == "none":
        return []
    return [text[0].lower() + text[1:]]


_SKILLS_ANY_RE = re.compile(r"^Choose\s+any\s+(\w+)$", re.IGNORECASE)
_SKILLS_FROM_RE = re.compile(
    r"^Choose\s+(\w+)(?:\s+skills?)?\s+from\s+(.+)$", re.IGNORECASE | re.DOTALL
)

# Universal headings the SRD prints in every class block but that the
# legacy CLASS_DATA only lists for cleric (so that owner-resolution in
# parse_features has at least one definitive owner; the runtime
# _UNIVERSAL_FEATURES handles the per-class reprints). Match that
# divergence so the extractor's output is byte-identical with the
# snapshot.
_ASI = "Ability Score Improvement"
_CLASSES_KEEPING_ASI = frozenset({"cleric"})

# Spellcasting ability detection lives in the feature body text — every
# caster class has a "<Ability> is your spellcasting ability for your
# <class> spells" sentence in its Spellcasting (or Pact Magic) feature.
_SPELLCASTING_ABILITY_RE = re.compile(
    r"(Charisma|Wisdom|Intelligence)\s+is\s+your\s+spellcasting\s+ability",
    re.IGNORECASE,
)
_ABILITY_ABBR: dict[str, str] = {
    "charisma": "Cha",
    "wisdom": "Wis",
    "intelligence": "Int",
}


def _extract_features_and_subclasses(
    class_spans: list[tuple[str, float, str, tuple]],
    class_simple: str,
) -> tuple[list[str], list[str]]:
    """Return ``(features, subclasses)`` derived from 13.9pt headings.

    Algorithm: collect every 13.9pt GillSans-SemiBold heading in PDF
    order across the class's page range. The last one is the subclass
    section heading; the rest are class features. Drop ``Ability Score
    Improvement`` from the features list for every class except cleric
    (see ``_CLASSES_KEEPING_ASI``).

    Feature IDs are unqualified (``feature:rage``) — the consumer
    ``parse_classes._qualify_feature_ids()`` rewrites them to
    ``feature:{owner}:rage``.
    """
    headings: list[str] = []
    for txt, sz, font, _ in class_spans:
        if sz == 13.9 and "GillSans" in font and txt:
            headings.append(txt)
    if not headings:
        return [], []
    *feature_headings, subclass_heading = headings
    if class_simple not in _CLASSES_KEEPING_ASI:
        feature_headings = [h for h in feature_headings if h != _ASI]
    features = [f"feature:{normalize_id(h)}" for h in feature_headings]
    subclasses = [f"subclass:{normalize_id(subclass_heading)}"]
    return features, subclasses


def _extract_spellcasting(
    class_spans: list[tuple[str, float, str, tuple]],
    class_simple: str,
) -> dict[str, str] | None:
    """Return ``{'ability': 'Wis', 'spell_list': 'cleric'}`` for caster classes.

    Detection: scan all 9.8pt Cambria body spans in the class's page
    range for a single sentence matching
    ``/<Ability> is your spellcasting ability/`` (verified to fire
    exactly once for each of the 8 SRD caster classes: bard, cleric,
    druid, paladin, ranger, sorcerer, warlock, wizard — and zero times
    for the 4 non-casters). The spell list always matches the class's
    simple_name.
    """
    body = " ".join(txt for txt, sz, font, _ in class_spans if sz == 9.8 and "Cambria" in font)
    m = _SPELLCASTING_ABILITY_RE.search(body)
    if m is None:
        return None
    return {
        "ability": _ABILITY_ABBR[m.group(1).lower()],
        "spell_list": class_simple,
    }


def _parse_skills(text: str) -> dict[str, Any]:
    """Parse the "Choose N from ..." / "Choose any N" shapes the SRD uses."""
    text = text.strip()
    m_any = _SKILLS_ANY_RE.match(text)
    if m_any:
        word = m_any.group(1).lower()
        return {"choose": _NUMBER_WORDS.get(word, 0), "from": ["any"]}
    m = _SKILLS_FROM_RE.match(text)
    if not m:
        return {"choose": 0, "from": []}
    count_word = m.group(1).lower()
    list_text = m.group(2).strip().rstrip(".")
    list_text = re.sub(r",\s+and\s+", ", ", list_text)
    list_text = re.sub(r"\s+and\s+", ", ", list_text)
    items = [p.strip() for p in list_text.split(",") if p.strip()]
    return {"choose": _NUMBER_WORDS.get(count_word, 0), "from": items}


# ---------------------------------------------------------------------------
# Progression table extraction
# ---------------------------------------------------------------------------

_LEVEL_RE = re.compile(r"^(\d+)(?:st|nd|rd|th)$")
# Empty-cell markers PyMuPDF returns for the SRD's table dashes.
# U+0336 is "combining longest stroke overlay" — the SRD renders empty
# Features cells with a dash glyph that pymupdf decodes to this combining
# character (alone, with no preceding base char).
_EMPTY_CELL_MARKERS = frozenset({"—", "-", "\u0336", "\u0336 ", " \u0336"})

# Cells the SRD PDF genuinely fails to expose via any extraction path
# (verified via ``page.search_for()`` returning zero hits for the
# missing tail text — see ``tests/test_pdf_provenance.py``).
#
# Each entry maps ``simple_name -> {level: [features]}`` and overrides
# the bbox-walk output. Keep this map small — every entry needs a
# search_for() reproducer that fails on the SRD PDF.
_PROGRESSION_FIXES: dict[str, dict[int, list[str]]] = {
    # Barbarian L11 cell (pi=7): "Relentless Rage" wraps to two lines
    # but the second line "Rage" is never extracted by any PyMuPDF API
    # — ``search_for("Relentless Rage")`` returns 0 hits on the page.
    "barbarian": {11: ["Relentless Rage"]},
    # Ranger L8 cell (pi=34): "Land's Stride" — only the first word
    # "Land" is extractable (the curly apostrophe + " Stride" tail
    # never appears in any 8.9pt Calibri span at the L8 row y).
    "ranger": {8: ["Ability Score Improvement", "Land's Stride"]},
    # Rogue L10 cell (pi=38): "Improvement" never surfaces in the L10
    # row — only "Ability Score" extracts. Other "Improvement"
    # occurrences exist on the page, just not at y > 688.
    "rogue": {10: ["Ability Score Improvement"]},
    # Wizard L20 cell (pi=52): "Signature Spells" — trailing "s" lost
    # in PDF rendering, only "Signature Spell" extracts from the cell.
    "wizard": {20: ["Signature Spells"]},
}


def _extract_progression(
    spans: list[tuple[str, float, str, tuple]],
    simple_name: str,
) -> list[dict[str, Any]]:
    """Return ``[{"level": 1, "features": [...]}, ...]`` for the class.

    Walks the per-class first-page progression table by bbox: the
    Features column is anchored by the 8.9pt Calibri-Bold "Features"
    header's x0, and only cells whose x0 matches that anchor (±3pt)
    are considered part of the column. Rows are bounded vertically by
    consecutive level-cell y-coordinates within the same visual column
    instance (the SRD lays the table out across two newspaper-style
    columns on most class pages).

    Applies ``_PROGRESSION_FIXES`` for cells the PDF genuinely fails to
    expose (each fix is reproducer-backed in
    ``tests/test_pdf_provenance.py``).
    """
    # 1. Locate the Features header and its column anchor x.
    bold_headers = [(t, b) for t, sz, f, b in spans if sz == 8.9 and f == "Calibri-Bold"]
    features_headers = [(t, b) for t, b in bold_headers if t == "Features"]
    if not features_headers:
        return []

    fx_left = features_headers[0][1][0]

    # 2. Collect level cells (8.9pt Calibri non-bold matching r"\dN(st|nd|...)").
    level_cells: list[tuple[int, float, float]] = []
    for txt, sz, font, bbox in spans:
        if sz != 8.9 or "Bold" in font:
            continue
        m = _LEVEL_RE.match(txt)
        if m and (bbox[2] - bbox[0]) < 25:
            level_cells.append((int(m.group(1)), bbox[1], bbox[0]))
    if not level_cells:
        return []

    # 3. Cluster level cells into visual column instances by x0. The
    # SRD lays the progression table across up to two newspaper-style
    # columns on the same page; cells within a column are within a few
    # points of each other but columns are separated by >>100pt.
    # Compute one offset per cluster so cell-to-cluster mapping is
    # exact (a per-cell offset is unstable — e.g. "1st" sits at x=61.7
    # but "10th" sits at x=58.8 in the same left column).
    clusters = cluster_values_by_gap(
        (round(lc[2], 1) for lc in level_cells),
        max_gap=50,
    )
    cluster_anchors = [min(c) for c in clusters]

    # Validate clusters: warlock's spell-slot table has a "Slot Level"
    # column that also matches the level-cell regex but isn't a
    # progression-table level column. Keep the largest cluster as the
    # primary, then accept additional clusters only when they
    # contribute levels not already covered (barbarian splits 1-11 and
    # 12-20 across two visual columns — both contribute new levels).
    cluster_levels: list[set[int]] = []
    for c in clusters:
        cluster_levels.append(
            {lvl for lvl, _, x in level_cells if any(abs(x - cx) < 0.5 for cx in c)}
        )
    order = sorted(range(len(clusters)), key=lambda i: -len(cluster_levels[i]))
    accepted: set[int] = set()
    covered: set[int] = set()
    for i in order:
        new_levels = cluster_levels[i] - covered
        if new_levels:
            accepted.add(i)
            covered |= new_levels
    clusters = [clusters[i] for i in sorted(accepted)]
    cluster_anchors = [min(c) for c in clusters]
    base_anchor = cluster_anchors[0]

    valid_xs = {cx for c in clusters for cx in c}
    level_cells = [lc for lc in level_cells if any(abs(lc[2] - vx) < 0.5 for vx in valid_xs)]

    def cluster_offset_for(level_x: float) -> float:
        for c, anchor in zip(clusters, cluster_anchors, strict=True):
            if any(abs(level_x - cx) < 0.5 for cx in c):
                return anchor - base_anchor
        return 0.0

    # 4. For each level, determine row bounds (top = own y0 - 1pt,
    # bottom = next level's y0 in same cluster - 1pt, or +30pt slack
    # for the final row).
    level_cells_sorted = sorted(level_cells, key=lambda lc: lc[0])

    by_cluster: dict[float, list[tuple[int, float]]] = {}
    for lvl, y, x in level_cells:
        key = cluster_offset_for(x)
        by_cluster.setdefault(key, []).append((lvl, y))
    for rows in by_cluster.values():
        rows.sort(key=lambda iy: iy[1])

    progression: list[dict[str, Any]] = []
    for lvl, y, x in level_cells_sorted:
        offset = cluster_offset_for(x)
        ix_left = fx_left + offset
        cluster_rows = by_cluster[offset]
        next_y = next((ly for li, ly in cluster_rows if ly > y + 0.5), None)
        y_top = y - 1.0
        y_bottom = (next_y - 1.0) if next_y is not None else (y + 30.0)

        # 5. Collect Calibri cell spans whose x0 sits in the Features
        # column. Features cells are left-aligned at exactly ``fx_left``;
        # mid-row continuation spans (the apostrophe span of
        # ``"Thieves' Cant"``, etc.) can land up to ~30pt to the right
        # but stay inside the ~80pt-wide column. Adjacent-column
        # overflow (e.g. "Unlimited" in Rages at barbarian L20) starts
        # at >60pt past the anchor, so a 30pt window keeps both
        # behaviors correct.
        cell_parts: list[tuple[float, float, str]] = []
        for txt, sz, font, bbox in spans:
            if sz != 8.9 or "Bold" in font or "Cambria" in font:
                continue
            bx, by = bbox[0], bbox[1]
            if -3.0 <= (bx - ix_left) <= 30.0 and y_top <= by < y_bottom:
                cell_parts.append((by, bx, txt))
        # Sort by y-bin (2pt buckets) then x so that punctuation spans
        # at slightly different y (e.g. the curly apostrophe in
        # "Thieves' Cant" sits 0.6pt below "Thieves" and "Cant") join
        # in left-to-right reading order on the same visual line.
        cell_parts.sort(key=lambda part: (round(part[0] / 2.0), part[1]))
        cell_text = " ".join(t for _, _, t in cell_parts).strip()

        override = _PROGRESSION_FIXES.get(simple_name, {}).get(lvl)
        if override is not None:
            features = override
        else:
            features = _parse_progression_features(cell_text)
        progression.append({"level": lvl, "features": features})

    progression.sort(key=lambda r: r["level"])
    return progression


_PROG_SPLIT_RE = re.compile(r",\s+(?![^()]*\))")
# Repair patterns for cell-text artifacts the PyMuPDF span split
# introduces:
#  - ``Ki- Empowered`` → ``Ki-Empowered``: a soft hyphen + U+2010
#    hyphen sequence becomes a hyphen + space after ``clean_text``.
#  - ``Thieves ' Cant`` → ``Thieves' Cant``: a curly apostrophe lives
#    in its own span (HiraKakuPro-W3 font) so the y-binned join
#    inserts a stray space on each side.
_PROG_HYPHEN_FIX_RE = re.compile(r"(\w)-\s+(\w)")
_PROG_APOS_FIX_RE = re.compile(r"\s+([\u2019'])")


def _parse_progression_features(text: str) -> list[str]:
    """Split a Features-cell string into a feature list.

    - Empty / dash markers → ``[]``.
    - Commas inside parentheses (e.g. "Brutal Critical (1 die)") are
      preserved.
    - Smart quotes get normalized by ``clean_text``.
    - Hyphen + space artifacts from PDF line wrapping are healed.
    """
    text = clean_text(text).strip()
    if not text or text in _EMPTY_CELL_MARKERS:
        return []
    text = _PROG_HYPHEN_FIX_RE.sub(r"\1-\2", text)
    text = _PROG_APOS_FIX_RE.sub(r"\1", text)
    parts = [p.strip() for p in _PROG_SPLIT_RE.split(text) if p.strip()]
    return parts
