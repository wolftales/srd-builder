"""Per-source extraction profiles.

The prose path in the SRD pipeline is tuned to one document: known headers, fixed
page ranges, source-specific fonts. That is not reusable for arbitrary
publications. The reusable seam sits lower - layout and span primitives - with a
declarative profile above it saying what this publication's typography means.

A profile carries no logic. It is data about one source, so that adding a second
publication adds a profile rather than a branch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# What a block of prose is for. Mirrors contentBlock.type in the package schema.
READ_ALOUD = "read_aloud"
GM_DETAIL = "gm_detail"

# Which audience may see it. Mirrors contentBlock.audience.
PLAYER_SAFE = "player_safe"
GM_ONLY = "gm_only"

AUDIENCE_BY_BLOCK_TYPE = {READ_ALOUD: PLAYER_SAFE, GM_DETAIL: GM_ONLY}

# Roles a line can play inside a statblock region.
STATBLOCK_NAME = "name"  # the creature's name, starting a new statblock
STATBLOCK_SECTION = "section"  # "Actions", "Reactions"
STATBLOCK_META = "meta"  # "Medium fiend, chaotic evil"
STATBLOCK_LABELLED = "labelled"  # "Armor Class 14 (natural armor)"
STATBLOCK_ABILITY_HEADER = "ability_header"  # "STR"
STATBLOCK_ABILITY_VALUE = "ability_value"  # "9 (-1)"
STATBLOCK_ENTRY_NAME = "entry_name"  # "Claw. Melee Weapon Attack: ..."
STATBLOCK_BODY = "body"  # continuation of the previous entry


@dataclass(frozen=True)
class SourceProfile:
    """How one publication's typography maps onto content roles.

    `body_fonts` maps a font name to the block type it carries. `heading_fonts`
    are display faces that mark structure rather than content. `column_split_x`
    is the page x-coordinate separating a two-column layout; None means one
    column.

    `overprinted_fonts` name faces the publication draws twice at an identical
    bounding box - a rendering effect, not duplicated content. Lines in those
    faces are deduplicated by geometry. This is recorded per profile rather than
    applied globally because it is a property of how one document was produced.
    """

    key: str
    ruleset: str
    body_fonts: dict[str, str]
    heading_fonts: frozenset[str] = field(default_factory=frozenset)
    overprinted_fonts: frozenset[str] = field(default_factory=frozenset)
    column_split_x: float | None = None
    #: Font roles are REGION-SCOPED, not document-wide. The same faces that carry
    #: read-aloud and GM prose in a keyed location carry statblock fields in the
    #: appendix, so `body_fonts` describes narrative regions only and a statblock
    #: region is read with `statblock_roles` instead. Discovered by importing the
    #: appendix: a flat font-to-role map silently misreads it as prose.
    statblock_roles: dict[tuple[str, float], str] = field(default_factory=dict)
    #: Outline title marking the start of the statblock appendix.
    appendix_pattern: str = r"^Appendix"
    # Regex naming a keyed location in a bookmark title, e.g. "G-3. Wayfarer's Rest Inn".
    key_pattern: str = r"^(?P<key>[A-Z]{1,2}-\d{1,3})\.\s*(?P<title>.+)$"

    def block_type(self, font: str) -> str | None:
        """The block type this font carries, or None if it is not body text."""
        return self.body_fonts.get(font)

    def is_heading(self, font: str) -> bool:
        return font in self.heading_fonts


# Frog God Games, Grimmsgate (5e) 2020. Typography confirmed by probing the
# source: CenturySchoolbook carries boxed read-aloud description,
# TimesNewRomanPSMT carries GM explanation, and the Caslon display face is drawn
# twice per line at an identical bbox.
GRIMMSGATE_5E = SourceProfile(
    key="grimmsgate_5e",
    ruleset="srd_5_1",
    body_fonts={
        "CenturySchoolbook": READ_ALOUD,
        "CenturySchoolbook-Bold": READ_ALOUD,
        "CenturySchoolbook-BoldIt": READ_ALOUD,
        "TimesNewRomanPSMT": GM_DETAIL,
        "TimesNewRomanPS-BoldMT": GM_DETAIL,
        "TimesNewRomanPS-ItalicMT": GM_DETAIL,
        "Times-Roman": GM_DETAIL,
    },
    heading_fonts=frozenset({"CaslonAntiqueEF-SC700", "CenturyGothic-SC700", "CenturyGothic"}),
    overprinted_fonts=frozenset({"CaslonAntiqueEF-SC700", "CenturyGothic-SC700"}),
    column_split_x=307.0,
    # Within the appendix the same faces mean something else entirely. Keyed by
    # (font, size) because the display face marks both a statblock's name and its
    # section headers, distinguished only by point size.
    statblock_roles={
        ("CaslonAntiqueEF-SC700", 13.0): STATBLOCK_NAME,
        ("CaslonAntiqueEF-SC700", 11.0): STATBLOCK_SECTION,
        ("Georgia-Italic", 9.0): STATBLOCK_META,
        ("CenturySchoolbook-Bold", 9.0): STATBLOCK_LABELLED,
        ("TimesNewRomanPS-BoldMT", 9.0): STATBLOCK_ABILITY_HEADER,
        ("TimesNewRomanPSMT", 9.0): STATBLOCK_ABILITY_VALUE,
        ("CenturySchoolbook-BoldIt", 9.0): STATBLOCK_ENTRY_NAME,
        ("CenturySchoolbook-Italic", 9.0): STATBLOCK_BODY,
        ("CenturySchoolbook", 9.0): STATBLOCK_BODY,
    },
)

PROFILES = {GRIMMSGATE_5E.key: GRIMMSGATE_5E}
