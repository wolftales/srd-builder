"""Resolving creature mentions in location text to rules records.

Two resolution modes, with different warrant.

A module-supplied creature is marked by the publication itself - this source
writes "(see Appendix)" beside it - so linking it is `source_explicit`.

A core creature is resolved by matching a name against the installed ruleset
bundle. That is a name match, not a statement: prose mentioning a skeleton is
not necessarily an encounter with one. Those links are `source_inferred`, and
the strip invariant means nothing built on them can be load-bearing.

The bundle namespace is looked up, never constructed. The SRD bundle files
creatures under `monster:`, `npc:` and `creature:` with no rule connecting a
name to its namespace, so an importer that emits `monster:<slug>` by convention
produces dangling references for every NPC and beast in the document.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from srd_builder.module_import.spine import slugify

#: Namespaces the SRD bundle files creatures under.
CREATURE_NAMESPACES = ("monster", "npc", "creature")

#: The publication's own marker that a creature is supplied by its appendix.
APPENDIX_MARKER = re.compile(r"\(\s*see\s+appendix\s*\)", re.IGNORECASE)

_QUANTITY_BEFORE = re.compile(r"(?P<quantity>\d+)\s+$")


@dataclass(frozen=True)
class Mention:
    """One creature named in a location's text."""

    name: str
    target: str  # bundle id or module supplement id
    quantity: int | None
    explicit: bool  # the publication marked it, rather than the importer matching a name

    @property
    def stance(self) -> str:
        return "source_explicit" if self.explicit else "source_inferred"


def bundle_creature_index(bundle_dir: Path) -> dict[str, str]:
    """Map creature name to its bundle id, by reading the bundle.

    A lookup, not a naming convention. Returns an empty index when the bundle is
    not built, so callers degrade to appendix-only resolution.
    """
    index: dict[str, str] = {}
    if not bundle_dir.is_dir():
        return index
    for path in sorted(bundle_dir.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for item in document.get("items", []):
            if not isinstance(item, dict):
                continue
            identifier, name = item.get("id"), item.get("name")
            if not isinstance(identifier, str) or not isinstance(name, str):
                continue
            if identifier.split(":", 1)[0] in CREATURE_NAMESPACES:
                index.setdefault(name.lower(), identifier)
    return index


def name_variants(name: str) -> list[str]:
    """A creature name and the plural forms this publication uses for it.

    Both plural forms are always offered, never one or the other. "Ash Human"
    ends in "man" but pluralizes as "ash humans", so treating the -man rule as
    an alternative to the regular -s rule silently stops matching it - the
    generated "ash humen" appears nowhere, and the creature goes undetected
    with no error.
    """
    lowered = name.lower()
    variants = [lowered]
    if not lowered.endswith("s"):
        variants.append(f"{lowered}s")
    if lowered.endswith("man"):
        variants.append(f"{lowered[:-3]}men")
    return list(dict.fromkeys(variants))


def build_creature_relationship(mention: Mention, location: str, rules_ref: str) -> dict[str, Any]:
    """The location-to-creature link, recorded whether or not a count is stated.

    A keyed location naming a creature is a fact worth keeping even when the
    publication does not say how many; without this the link exists only when a
    quantity happens to be printed.
    """
    return {
        "id": f"relationship:{slugify(location)}_features_{slugify(mention.name)}",
        "view": "reference",
        "type": "features_creature",
        "stance": mention.stance,
        "from_ref": location,
        "to_ref": rules_ref,
    }


def find_mentions(text: str, *, supplements: dict[str, str], core: dict[str, str]) -> list[Mention]:
    """Every creature named in `text`, longest name first so it wins.

    Module supplements are checked before core records: a publication that
    supplies its own version of a creature means that one, not the SRD's.
    """
    found: dict[str, Mention] = {}
    claimed: list[tuple[int, int]] = []

    def overlaps(start: int, end: int) -> bool:
        return any(start < prior_end and prior_start < end for prior_start, prior_end in claimed)

    candidates = [(name, target, True) for name, target in supplements.items()]
    candidates += [(name, target, False) for name, target in core.items()]
    # Longest first so "bandit captain" is not consumed by "bandit".
    candidates.sort(key=lambda item: -len(item[0]))

    for name, target, is_supplement in candidates:
        for variant in name_variants(name):
            for match in re.finditer(rf"\b{re.escape(variant)}\b", text, re.IGNORECASE):
                if overlaps(match.start(), match.end()):
                    continue
                claimed.append((match.start(), match.end()))
                quantity_match = _QUANTITY_BEFORE.search(text[: match.start()])
                quantity = int(quantity_match.group("quantity")) if quantity_match else None
                # The marker follows the name, so look just past the match.
                trailing = text[match.end() : match.end() + 40]
                explicit = is_supplement and bool(APPENDIX_MARKER.search(trailing))

                existing = found.get(target)
                if existing is None or (quantity is not None and existing.quantity is None):
                    found[target] = Mention(
                        name=name,
                        target=target,
                        quantity=quantity,
                        explicit=explicit or (existing.explicit if existing else False),
                    )
                elif explicit and not existing.explicit:
                    found[target] = Mention(
                        name=existing.name,
                        target=existing.target,
                        quantity=existing.quantity,
                        explicit=True,
                    )
    return sorted(found.values(), key=lambda mention: mention.target)


def build_rules_reference(mention: Mention) -> dict[str, Any]:
    """A link to a creature in the installed ruleset bundle."""
    return {
        "id": f"rules_ref:{slugify(mention.target)}",
        "target": mention.target,
        "stance": mention.stance,
    }


def build_actor_group(
    mention: Mention, rules_ref: str, location_key: str, page_label: str
) -> dict[str, Any]:
    """A body of interchangeable creatures the source says is here.

    Only built when the publication states a count. Inventing a quantity would
    put a number in front of a GM that the source never printed.
    """
    slug = f"{slugify(location_key)}_{slugify(mention.name)}"
    return {
        "id": f"group:{slug}",
        "type": "actor_group",
        "stance": mention.stance,
        "quantity": mention.quantity,
        "rules_ref": rules_ref,
        "source_ref": {"source_key": location_key, "printed_page": page_label},
    }


def build_placement(group_id: str, location_id: str, stance: str) -> dict[str, Any]:
    return {
        "id": f"placement:{group_id.split(':', 1)[1]}",
        "type": "placement",
        "group_ref": group_id,
        "location_ref": location_id,
        "stance": stance,
        "presence": "initial",
    }
