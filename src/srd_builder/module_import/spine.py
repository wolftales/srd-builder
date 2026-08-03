"""Publication structure from the source's own navigation. Pure functions.

The publication spine is how the document is organized and read. It is not the
physical-location graph, and the two must not be conflated.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from srd_builder.module_import.profile import SourceProfile
from srd_builder.module_import.source import TocEntry


def slugify(text: str) -> str:
    """A stable, id-safe token. Typographic quotes and punctuation are dropped."""
    ascii_text = text.replace("’", "").replace("‘", "").replace("—", " ")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text.lower()).strip("_")
    return slug or "untitled"


@dataclass(frozen=True)
class KeyedEntry:
    """A bookmark that names a keyed location, e.g. "G-3. Wayfarer's Rest Inn"."""

    key: str  # "G-3"
    title: str  # "Wayfarer's Rest Inn"
    page_index: int  # 0-based
    node_id: str


def _path_id(ancestors: list[str], title: str) -> str:
    """Path-based so repeated titles stay distinct.

    "Map Key" appears three times in this publication - once per section. A
    title-derived id would collide; the path through the outline does not.
    """
    return "pub:" + "/".join([*ancestors, slugify(title)])


def _walk_outline(
    toc: list[TocEntry] | tuple[TocEntry, ...],
) -> list[tuple[TocEntry, str, str | None]]:
    """Each entry with its path-based id and its parent's id."""
    walked: list[tuple[TocEntry, str, str | None]] = []
    by_level: dict[int, str] = {}
    ancestors_by_level: dict[int, list[str]] = {}

    for entry in toc:
        ancestors = ancestors_by_level.get(entry.level - 1, [])
        node_id = _path_id(ancestors, entry.title)
        walked.append((entry, node_id, by_level.get(entry.level - 1)))

        by_level[entry.level] = node_id
        ancestors_by_level[entry.level] = [*ancestors, slugify(entry.title)]
        # Deeper levels from a previous branch must not be inherited.
        for level in [lvl for lvl in by_level if lvl > entry.level]:
            del by_level[level]
            ancestors_by_level.pop(level, None)
    return walked


def publication_nodes(toc: list[TocEntry] | tuple[TocEntry, ...]) -> list[dict[str, Any]]:
    """The outline as publication records, each linked to parent and children."""
    nodes: list[dict[str, Any]] = []

    for entry, node_id, parent_id in _walk_outline(toc):
        nodes.append(
            {
                "id": node_id,
                "type": "section",
                "title": entry.title,
                "children": [],
                "stance": "source_explicit",
                "source_ref": {"pdf_page": entry.page},
                **({"parent_ref": parent_id} if parent_id else {}),
            }
        )

    index = {node["id"]: node for node in nodes}
    for node in nodes:
        parent = index.get(node.get("parent_ref", ""))
        if parent is not None:
            parent["children"].append(node["id"])
    return nodes


def keyed_entries(
    toc: list[TocEntry] | tuple[TocEntry, ...], profile: SourceProfile
) -> list[KeyedEntry]:
    """Every bookmark naming a keyed location, in publication order."""
    pattern = re.compile(profile.key_pattern)
    found: list[KeyedEntry] = []
    for entry, node_id, _parent in _walk_outline(toc):
        match = pattern.match(entry.title.strip())
        if match:
            found.append(
                KeyedEntry(
                    key=match.group("key"),
                    title=match.group("title").strip(),
                    page_index=entry.page - 1,
                    node_id=node_id,
                )
            )
    return found


def location_id(key: str) -> str:
    """Stable identity comes from the source key, not from prose.

    Correcting a room description must not create a new room (D7), so the id is
    derived from the publication's own key rather than its title.
    """
    return f"location:{slugify(key)}"


def simple_name(title: str) -> str:
    """A short common noun for the location, inferred from its proper name.

    "Wayfarer's Rest Inn" -> "inn". This is an inference, not something the
    publication states, and callers mark it as such.
    """
    words = [word for word in re.split(r"\s+", title.strip()) if word]
    return slugify(words[-1]) if words else "location"
