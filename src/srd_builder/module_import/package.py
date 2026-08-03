"""Assembling a mountable module content package.

The package is the producer's output contract. It carries publication text, so
compiled packages belong under `build/` and never in the repository.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from srd_builder import __version__
from srd_builder.module_import.profile import SourceProfile
from srd_builder.module_import.source import PublicationIdentity
from srd_builder.module_import.spine import KeyedEntry, location_id, simple_name

SCHEMA_VERSION = "0.1.0"


@dataclass
class PackageContent:
    """The records a compile run produced, before they become a package.

    Grouped rather than passed individually: the collections grow together as
    the importer covers more of a publication, and threading each one through
    the assembler as its own parameter stops scaling almost immediately.
    """

    publication: list[dict[str, Any]] = field(default_factory=list)
    blocks: list[dict[str, Any]] = field(default_factory=list)
    locations: list[dict[str, Any]] = field(default_factory=list)
    actor_groups: list[dict[str, Any]] = field(default_factory=list)
    placements: list[dict[str, Any]] = field(default_factory=list)
    references: list[dict[str, Any]] = field(default_factory=list)
    supplements: list[dict[str, Any]] = field(default_factory=list)
    relationships: list[dict[str, Any]] = field(default_factory=list)


#: Collections the package schema requires. Every one is present even when this
#: slice has nothing to put in it, so the envelope stays valid as it fills in.
EMPTY_COLLECTIONS = (
    "actors",
    "objects",
    "tables",
    "active_features",
    "situations",
    "adaptation_points",
    "assets",
)


def build_location(
    entry: KeyedEntry, blocks: list[dict[str, Any]], page_label: str
) -> dict[str, Any]:
    """One keyed location, linked to the blocks printed under it."""
    return {
        "id": location_id(entry.key),
        "type": "location",
        "names": {"simple": simple_name(entry.title), "proper": entry.title},
        "content_refs": [block["id"] for block in blocks],
        "source_ref": {"source_key": entry.key, "printed_page": page_label},
        "stance": "source_explicit",
        # The publication prints a proper name; the short common noun for it is
        # the importer's reading of that name.
        "inferred_fields": ["names"],
    }


def build_supplement(
    record: dict[str, Any], profile: SourceProfile, *, page_label: str
) -> dict[str, Any]:
    """Wrap a lens-normalized creature in its package ownership envelope.

    The payload is whatever the selected ruleset lens produces, unchanged. A
    module supplement and an SRD monster are the same shape (D2); only the
    envelope says who owns this one.
    """
    return {
        "id": f"module_rules:{profile.key}:monster/{record['simple_name']}",
        "entity_type": "monster",
        "ruleset": profile.ruleset,
        "ownership": "module_supplement",
        "data": record,
        "source_ref": {"section": "appendix", "printed_page": page_label},
        "stance": "source_explicit",
    }


def _relationship_vocabulary(relationships: list[dict[str, Any]]) -> dict[str, list[str]]:
    """What the package declares about its own graph, derived from its edges."""
    vocabulary: dict[str, set[str]] = {}
    for relationship in relationships:
        vocabulary.setdefault(relationship["view"], set()).add(relationship["type"])
    return {view: sorted(types) for view, types in sorted(vocabulary.items())}


def build_package(
    identity: PublicationIdentity,
    profile: SourceProfile,
    content: PackageContent,
    *,
    title: str,
    content_version: str,
) -> dict[str, Any]:
    """A schema-valid package for the compiled slice."""
    return {
        "meta": {
            "package_id": f"module:{profile.key}",
            "title": title,
            "content_version": content_version,
            "schema_version": SCHEMA_VERSION,
            "builder_version": __version__,
            "ruleset": {"id": profile.ruleset, "lens_version": SCHEMA_VERSION},
            "source": {"format": "pdf", "fingerprint": identity.fingerprint},
            # Declared even when empty: the package describes its own vocabulary,
            # and an absent declaration is not the same as an empty one.
            "relationship_vocabulary": _relationship_vocabulary(content.relationships),
            "state_vocabulary": {},
        },
        "publication": content.publication,
        "blocks": content.blocks,
        "locations": content.locations,
        "actor_groups": content.actor_groups,
        "placements": content.placements,
        "relationships": content.relationships,
        **{name: [] for name in EMPTY_COLLECTIONS},
        "rules": {
            "references": content.references,
            "supplements": content.supplements,
            "procedures": [],
        },
    }
