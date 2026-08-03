"""Assembling a mountable module content package.

The package is the producer's output contract. It carries publication text, so
compiled packages belong under `build/` and never in the repository.
"""

from __future__ import annotations

from typing import Any

from srd_builder import __version__
from srd_builder.module_import.profile import SourceProfile
from srd_builder.module_import.source import PublicationIdentity
from srd_builder.module_import.spine import KeyedEntry, location_id, simple_name

SCHEMA_VERSION = "0.1.0"

#: Collections the package schema requires. Every one is present even when this
#: slice has nothing to put in it, so the envelope stays valid as it fills in.
EMPTY_COLLECTIONS = (
    "actors",
    "actor_groups",
    "placements",
    "objects",
    "tables",
    "active_features",
    "situations",
    "relationships",
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


def build_package(
    identity: PublicationIdentity,
    profile: SourceProfile,
    *,
    title: str,
    publication: list[dict[str, Any]],
    blocks: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    content_version: str,
    supplements: list[dict[str, Any]] | None = None,
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
            "relationship_vocabulary": {},
            "state_vocabulary": {},
        },
        "publication": publication,
        "blocks": blocks,
        "locations": locations,
        **{name: [] for name in EMPTY_COLLECTIONS},
        "rules": {"references": [], "supplements": supplements or [], "procedures": []},
    }
