"""Checks for the module-content importer.

Two layers. The pure-function tests run everywhere, including CI, because they
work on synthetic inputs. The live tests need the source publication and skip
cleanly without it, matching the `srd_5_1_pdf` fixture's behaviour.

Live tests assert on STRUCTURE only - counts, ids, types, audience, ordering.
They never assert on extracted prose. The source is a third-party commercial
publication, and pinning its text in an assertion would commit that text to the
repository through the back door.

For the same reason the pure tests use synthetic titles rather than the
publication's own room names. They exercise the same code paths, and a source
key like "G-3" is a structural identifier the importer must be driven by, not
content.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from srd_builder.module_import import blocks as block_builder
from srd_builder.module_import import source as source_io
from srd_builder.module_import import spine, statblocks
from srd_builder.module_import.compile import compile_location_slice
from srd_builder.module_import.profile import GRIMMSGATE_5E, SourceProfile
from srd_builder.module_import.source import TocEntry

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "docs" / "planning" / "module_content_prototype" / "schemas"
SLICE_KEY = "G-3"


@pytest.fixture(scope="module")
def package_validator() -> Draft202012Validator:
    documents = [
        json.loads(path.read_text(encoding="utf-8")) for path in sorted(SCHEMAS.glob("*.json"))
    ]
    registry = Registry().with_resources(
        (doc["$id"], Resource.from_contents(doc, default_specification=DRAFT202012))
        for doc in documents
        if "$id" in doc
    )
    envelope = json.loads((SCHEMAS / "module-package.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(envelope, registry=registry)


@pytest.fixture(scope="module")
def source_path() -> Path:
    try:
        return source_io.resolve_source_path()
    except source_io.SourceUnavailableError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="module")
def compiled_slice(source_path: Path) -> dict[str, Any]:
    return compile_location_slice(source_path, GRIMMSGATE_5E, SLICE_KEY)


# --------------------------------------------------------------------------
# Pure functions - no publication required
# --------------------------------------------------------------------------


def test_slugify_drops_typographic_punctuation() -> None:
    assert spine.slugify("Warden’s Gatehouse") == "wardens_gatehouse"
    assert spine.slugify("T-38. Signal Chamber") == "t_38_signal_chamber"
    assert spine.slugify("!!!") == "untitled"


def test_publication_ids_are_path_based_so_repeated_titles_stay_distinct() -> None:
    """ "Map Key" appears once per section; a title-derived id would collide."""
    toc = [
        TocEntry(1, "The Village", 6),
        TocEntry(2, "Map Key", 6),
        TocEntry(1, "The Wilderness", 9),
        TocEntry(2, "Map Key", 9),
    ]
    nodes = spine.publication_nodes(toc)
    ids = [node["id"] for node in nodes]

    assert len(set(ids)) == len(ids)
    assert ids[1] == "pub:the_village/map_key"
    assert ids[3] == "pub:the_wilderness/map_key"
    assert nodes[0]["children"] == ["pub:the_village/map_key"]
    assert nodes[3]["parent_ref"] == "pub:the_wilderness"


def test_outline_does_not_inherit_a_previous_branch_depth() -> None:
    toc = [
        TocEntry(1, "Village", 6),
        TocEntry(2, "Key", 6),
        TocEntry(3, "G-1. Farmhouse", 6),
        TocEntry(1, "Wilderness", 9),
        TocEntry(2, "Key", 9),
    ]
    nodes = {node["id"]: node for node in spine.publication_nodes(toc)}
    assert nodes["pub:wilderness/key"]["parent_ref"] == "pub:wilderness"


def test_keyed_entries_recognize_the_publication_key_format() -> None:
    toc = [
        TocEntry(1, "The Village", 6),
        TocEntry(2, "G-3. Wayfarer's Rest Inn", 6),
        TocEntry(2, "Rumor Table", 6),
        TocEntry(2, "T-40. Lair of the Sunken Host", 20),
    ]
    found = spine.keyed_entries(toc, GRIMMSGATE_5E)

    assert [entry.key for entry in found] == ["G-3", "T-40"]
    assert found[0].title == "Wayfarer's Rest Inn"
    assert found[0].page_index == 5  # bookmarks are 1-based
    assert found[1].title == "Lair of the Sunken Host"


def test_identity_is_derived_from_the_source_key_not_the_title() -> None:
    """Correcting a room's description must not create a new room (D7)."""
    assert spine.location_id("G-3") == "location:g_3"
    assert spine.simple_name("Wayfarer's Rest Inn") == "inn"
    assert spine.simple_name("Lair of the Sunken Host") == "host"


def test_join_lines_repairs_line_break_hyphenation() -> None:
    assert block_builder.join_lines(["aban-", "doned now."]) == "abandoned now."
    assert block_builder.join_lines(["one   two", "", "  three "]) == "one two three"


def _profile(**overrides: Any) -> SourceProfile:
    base = {
        "key": "test",
        "ruleset": "srd_5_1",
        "body_fonts": {"Box": "read_aloud", "Body": "gm_detail"},
        "heading_fonts": frozenset({"Display"}),
    }
    return SourceProfile(**{**base, **overrides})


def _line(text: str, font: str) -> dict[str, Any]:
    return {"text": text, "font": font, "size": 9.0, "bbox": (0, 0, 1, 1), "column": 0}


def test_blocks_are_grouped_by_role_and_declare_audience_as_inferred() -> None:
    entry = spine.KeyedEntry(key="G-3", title="Inn", page_index=5, node_id="pub:x")
    lines = [
        _line("Description one.", "Box"),
        _line("Description two.", "Box"),
        _line("GM note.", "Body"),
        _line("Ignored caption.", "Unmapped"),
    ]
    blocks = block_builder.blocks_for_key(lines, entry, _profile(), "5")

    assert [b["type"] for b in blocks] == ["read_aloud", "gm_detail"]
    assert [b["audience"] for b in blocks] == ["player_safe", "gm_only"]
    assert blocks[0]["text"] == "Description one. Description two."
    # Typography implies who may hear it; that inference is always declared.
    assert all(b["inferred_fields"] == ["audience"] for b in blocks)
    assert all(b["stance"] == "source_explicit" for b in blocks)


def test_a_heading_breaks_a_run_of_the_same_role() -> None:
    entry = spine.KeyedEntry(key="G-3", title="Inn", page_index=5, node_id="pub:x")
    lines = [
        _line("First note.", "Body"),
        _line("A Subheading", "Display"),
        _line("Second note.", "Body"),
    ]
    blocks = block_builder.blocks_for_key(lines, entry, _profile(), "5")

    assert len(blocks) == 2
    assert [b["id"] for b in blocks] == ["block:g_3_gm_detail_1", "block:g_3_gm_detail_2"]


def test_slice_runs_from_one_key_to_the_next() -> None:
    stream = [
        _line("G-2. Gatehouse", "Display"),
        _line("Gatehouse prose.", "Body"),
        _line("G-3. Inn", "Display"),
        _line("Inn prose.", "Body"),
        _line("G-4. Stable", "Display"),
        _line("Stable prose.", "Body"),
    ]
    taken = block_builder.slice_for_key(stream, "G-3", "G-4")
    assert [line["text"] for line in taken] == ["Inn prose."]

    # A final key has no following key and runs to the end of the stream.
    assert [line["text"] for line in block_builder.slice_for_key(stream, "G-4", None)] == [
        "Stable prose."
    ]
    assert block_builder.slice_for_key(stream, "G-9", None) == []


def test_missing_source_configuration_refuses_rather_than_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Silently importing the wrong publication is worse than importing none."""
    monkeypatch.delenv(source_io.SOURCE_ENV_VAR, raising=False)
    with pytest.raises(source_io.SourceUnavailableError):
        source_io.resolve_source_path()
    with pytest.raises(source_io.SourceUnavailableError):
        source_io.resolve_source_path("/nonexistent/publication.pdf")


# --------------------------------------------------------------------------
# Live - requires the configured source publication
# --------------------------------------------------------------------------


def test_publication_identity_comes_from_the_file(source_path: Path) -> None:
    with source_io.open_source(source_path) as doc:
        identity = source_io.probe_identity(doc, source_path)
        evidence = source_io.ruleset_evidence(doc)

    assert identity.fingerprint.startswith("sha256:")
    assert len(identity.fingerprint) == len("sha256:") + 64
    assert identity.page_count > 0
    assert identity.has_navigation, "spine recovery depends on an outline"
    # Ruleset identity is established from the text, not the filename: a sibling
    # bundle ships a Swords & Wizardry edition of this same adventure.
    assert sum(evidence.values()) > 0


def test_compiled_slice_validates_against_the_package_schemas(
    compiled_slice: dict[str, Any], package_validator: Draft202012Validator
) -> None:
    assert list(package_validator.iter_errors(compiled_slice)) == []


def test_compiled_slice_answers_run_the_current_location(compiled_slice: dict[str, Any]) -> None:
    """R1: the location, its player-facing prose, and its GM-only prose."""
    locations = compiled_slice["locations"]
    assert len(locations) == 1
    location = locations[0]
    blocks = {block["id"]: block for block in compiled_slice["blocks"]}

    assert location["id"] == spine.location_id(SLICE_KEY)
    assert location["names"]["proper"]
    assert location["names"]["simple"]
    assert location["content_refs"], "a keyed location with no content is not runnable"
    assert set(location["content_refs"]) <= set(blocks)
    assert {blocks[ref]["audience"] for ref in location["content_refs"]} == {
        "player_safe",
        "gm_only",
    }


def test_compiled_slice_marks_typographic_inferences(compiled_slice: dict[str, Any]) -> None:
    for block in compiled_slice["blocks"]:
        assert block["inferred_fields"] == ["audience"]
    assert compiled_slice["locations"][0]["inferred_fields"] == ["names"]


def test_compiled_spine_covers_the_outline_with_unique_ids(
    compiled_slice: dict[str, Any], source_path: Path
) -> None:
    with source_io.open_source(source_path) as doc:
        identity = source_io.probe_identity(doc, source_path)

    nodes = compiled_slice["publication"]
    ids = [node["id"] for node in nodes]
    assert len(nodes) == len(identity.toc)
    assert len(set(ids)) == len(ids), "repeated bookmark titles must not collide"

    declared = set(ids)
    for node in nodes:
        assert set(node["children"]) <= declared
        if "parent_ref" in node:
            assert node["parent_ref"] in declared


def test_overprinted_headings_are_not_extracted_twice(compiled_slice: dict[str, Any]) -> None:
    """The display face is drawn twice per line at an identical bbox.

    Asserted structurally: no extracted block repeats its own opening words, which
    is what naive extraction produces without geometry-based deduplication.
    """
    for block in compiled_slice["blocks"]:
        opening = " ".join(block["text"].split()[:6])
        assert opening, block["id"]
        assert block["text"].count(opening) == 1, f"{block['id']} looks overprinted"


def test_every_keyed_location_in_the_publication_yields_content(source_path: Path) -> None:
    """A key that extracts nothing means the profile or the boundaries are wrong."""
    with source_io.open_source(source_path) as doc:
        identity = source_io.probe_identity(doc, source_path)
        entries = spine.keyed_entries(identity.toc, GRIMMSGATE_5E)

    assert len(entries) > 10, "the outline should expose many keyed locations"
    empty = []
    for entry in entries:
        package = compile_location_slice(source_path, GRIMMSGATE_5E, entry.key)
        if not package["blocks"]:
            empty.append(entry.key)
    assert empty == [], f"keyed locations extracted no content: {empty}"


# --------------------------------------------------------------------------
# Statblock appendix
# --------------------------------------------------------------------------


def test_appendix_range_is_bounded_by_outline_level_not_by_page() -> None:
    """The appendix's own children sit on later pages than its heading.

    A page-only boundary stops at the second creature and silently drops the
    rest, which is exactly what the first cut did.
    """
    toc = [
        TocEntry(1, "The Elder Temple", 9),
        TocEntry(1, "Appendix: New Monsters", 22),
        TocEntry(2, "First Creature", 22),
        TocEntry(2, "Second Creature", 23),
        TocEntry(2, "Third Creature", 24),
        TocEntry(1, "Legal Appendix", 25),
    ]
    assert statblocks.appendix_page_range(toc, GRIMMSGATE_5E, 26) == (21, 23)


def test_appendix_range_reports_when_no_appendix_exists() -> None:
    toc = [TocEntry(1, "The Village", 6)]
    with pytest.raises(ValueError, match="no statblock appendix"):
        statblocks.appendix_page_range(toc, GRIMMSGATE_5E, 26)


def test_negative_ability_modifiers_use_the_publication_en_dash() -> None:
    """The publication sets negative modifiers with an en dash, not a hyphen."""
    assert statblocks._parse_ability_value("9 (–1)") == {"value": 9, "modifier": -1}
    assert statblocks._parse_ability_value("15 (+2)") == {"value": 15, "modifier": 2}
    assert statblocks._parse_ability_value("10 (0)") == {"value": 10, "modifier": 0}
    assert statblocks._parse_ability_value("not a score") is None


def test_statblock_runs_split_on_the_creature_name_role() -> None:
    def line(text: str, font: str, size: float) -> dict[str, Any]:
        return {"text": text, "font": font, "size": size, "bbox": (0, 0, 1, 1), "column": 0}

    name_font, name_size = next(
        key for key, role in GRIMMSGATE_5E.statblock_roles.items() if role == "name"
    )
    body_font, body_size = next(
        key for key, role in GRIMMSGATE_5E.statblock_roles.items() if role == "body"
    )
    lines = [
        line("Ignored preamble", body_font, body_size),
        line("First", name_font, name_size),
        line("body a", body_font, body_size),
        line("Second", name_font, name_size),
    ]
    runs = statblocks.split_statblocks(lines, GRIMMSGATE_5E)

    assert len(runs) == 2
    assert [run[0]["text"] for run in runs] == ["First", "Second"]
    assert len(runs[0]) == 2  # name plus its body; the preamble is not adopted


def test_every_appendix_statblock_validates_against_the_production_lens(
    compiled_slice: dict[str, Any],
) -> None:
    """D2 made executable: a module supplement is an SRD monster in an envelope."""
    monster_schema = json.loads((ROOT / "schemas" / "monster.schema.json").read_text())
    validator = Draft202012Validator(monster_schema)
    supplements = compiled_slice["rules"]["supplements"]

    assert len(supplements) >= 8, "the publication's appendix should yield every creature"
    for supplement in supplements:
        assert supplement["ownership"] == "module_supplement"
        assert supplement["entity_type"] == "monster"
        assert supplement["id"].startswith("module_rules:")
        assert list(validator.iter_errors(supplement["data"])) == [], supplement["id"]


def test_supplements_carry_mechanics_not_just_names(compiled_slice: dict[str, Any]) -> None:
    """A supplement that parsed only a name would still validate; assert substance."""
    for supplement in compiled_slice["rules"]["supplements"]:
        data = supplement["data"]
        assert data["armor_class"]["value"] > 0
        assert len(data["ability_scores"]) == 6
        assert data["actions"], f"{supplement['id']} has no actions"
        for ability in data["ability_scores"].values():
            assert 1 <= ability["value"] <= 30
