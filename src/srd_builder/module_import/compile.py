"""Compile one keyed location from a source publication into a package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from srd_builder.module_import import blocks as block_builder
from srd_builder.module_import import source as source_io
from srd_builder.module_import import spine
from srd_builder.module_import import statblocks as statblock_reader
from srd_builder.module_import.package import build_location, build_package, build_supplement
from srd_builder.module_import.profile import SourceProfile
from srd_builder.parse.parse_monsters import normalize_monster


def _next_outline_page(toc: Any, after_index: int, page_count: int) -> int:
    """The page where the next outline entry starts, in page order.

    Outline order is not page order in this publication - a section's map is
    bookmarked before its map key - so boundaries are taken by page, not by
    position in the outline.
    """
    later = [entry.page - 1 for entry in toc if entry.page - 1 > after_index]
    return min(later) if later else page_count - 1


def compile_location_slice(
    path: Path, profile: SourceProfile, key: str, *, content_version: str = "slice.1"
) -> dict[str, Any]:
    """Import a single keyed location end to end.

    Deliberately narrow: it proves publication identity, spine recovery, block
    classification, and package assembly against a real publication without
    claiming to import the whole document.
    """
    with source_io.open_source(path) as doc:
        identity = source_io.probe_identity(doc, path)
        if not identity.has_navigation:
            raise ValueError(f"{path.name} has no outline; spine recovery needs one")

        entries = spine.keyed_entries(identity.toc, profile)
        index = next((i for i, entry in enumerate(entries) if entry.key == key), None)
        if index is None:
            raise KeyError(f"{key} is not a keyed location in {path.name}")
        entry = entries[index]
        following = entries[index + 1] if index + 1 < len(entries) else None

        # A keyed entry can run past its starting page, so read forward to
        # wherever the next key begins rather than assuming one page. The final
        # key has no following key, so its boundary is the next outline entry of
        # any kind - without this it would be truncated to its first page.
        last_page = (
            following.page_index
            if following
            else _next_outline_page(identity.toc, entry.page_index, identity.page_count)
        )
        reading_order: list[dict[str, Any]] = []
        for page_index in range(entry.page_index, min(last_page + 1, identity.page_count)):
            reading_order.extend(source_io.page_lines(doc, page_index, profile))

        lines = block_builder.slice_for_key(
            reading_order, entry.key, following.key if following else None
        )
        page_label = str(entry.page_index + 1)
        extracted = block_builder.blocks_for_key(lines, entry, profile, page_label)
        location = build_location(entry, extracted, page_label)

        supplements = compile_appendix(doc, identity, profile)

        return build_package(
            identity,
            profile,
            title=identity.path.stem,
            publication=spine.publication_nodes(identity.toc),
            blocks=extracted,
            locations=[location],
            content_version=content_version,
            supplements=supplements,
        )


def write_package(package: dict[str, Any], destination: Path) -> Path:
    """Write a compiled package. Callers must target an ignored build location."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return destination


def compile_appendix(doc: Any, identity: Any, profile: SourceProfile) -> list[dict[str, Any]]:
    """Every module-supplied creature in the publication's statblock appendix.

    Extraction is source-specific; normalization is the selected ruleset lens,
    reused verbatim from SRD monster parsing so both go through one contract.
    """
    try:
        start, end = statblock_reader.appendix_page_range(
            identity.toc, profile, identity.page_count
        )
    except ValueError:
        return []

    lines = [
        line
        for page_index in range(start, end + 1)
        for line in source_io.page_lines(doc, page_index, profile)
    ]

    supplements: list[dict[str, Any]] = []
    for run in statblock_reader.split_statblocks(lines, profile):
        raw = statblock_reader.parse_statblock(run, profile)
        raw["simple_name"] = spine.slugify(raw["name"])
        raw["id"] = f"monster:{raw['simple_name']}"
        supplements.append(
            build_supplement(normalize_monster(raw), profile, page_label=str(start + 1))
        )
    return supplements
