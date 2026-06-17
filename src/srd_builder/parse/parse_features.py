"""Parse extracted feature data into structured feature records.

Pure parsing module (no I/O) - takes raw feature data and returns
structured feature records matching the feature schema.
"""

from __future__ import annotations

import re
from typing import Any

from srd_builder.postprocess.ids import normalize_id
from srd_builder.rulesets.srd_5_1.class_targets import CLASS_DATA
from srd_builder.rulesets.srd_5_1.lineage_targets import LINEAGE_DATA

_WHITESPACE_RE = re.compile(r"\s+")


def parse_features(
    raw_features: dict[str, Any], source_type: str = "class"
) -> list[dict[str, Any]]:
    """Parse raw feature data into structured feature records.

    Args:
        raw_features: Raw features from extract_features()
        source_type: "class" or "lineage" for appropriate ID prefix

    Returns:
        List of structured feature dicts matching feature schema
    """
    accepted: list[dict[str, Any]] = []
    for raw in raw_features.get("features", []):
        name = _WHITESPACE_RE.sub(" ", raw["name"]).strip()
        text = raw["text"]
        if len(text) < 20:
            continue
        if _is_section_header(name):
            continue
        accepted.append(
            {
                "name": name,
                "simple_name": _create_simple_name(name),
                "text": text,
                "page": raw["page"],
            }
        )

    owners = _resolve_owners(accepted, source_type)

    features: list[dict[str, Any]] = []
    for entry, (owner_kind, owner_simple) in zip(accepted, owners, strict=True):
        if owner_simple is None:
            continue
        feature = {
            "id": f"feature:{owner_simple}:{entry['simple_name']}",
            "name": entry["name"],
            "simple_name": entry["simple_name"],
            "owner_id": f"{owner_kind}:{owner_simple}",
            "page": entry["page"],
            "source": raw_features.get("source", "SRD 5.1"),
            "text": entry["text"],
        }
        summary = _extract_summary(entry["text"])
        if summary:
            feature["summary"] = summary
        features.append(feature)

    return features


def _is_section_header(name: str) -> bool:
    """Check if this is a section header not an actual feature.

    Args:
        name: Feature name

    Returns:
        True if this is a section header
    """
    headers = [
        "Racial Traits",
        "Dwarf Traits",
        "Elf Traits",
        "Halfling Traits",
        "Human Traits",
        "Dragonborn Traits",
        "Gnome Traits",
        "Half-Elf Traits",
        "Half-Orc Traits",
        "Tiefling Traits",
        "Class Features",
        "Hit Points",
        "Proficiencies",
        "Equipment",
    ]

    return name in headers


def _create_simple_name(name: str) -> str:
    """Create simple_name from feature name.

    Delegates to the canonical normalize_id so hyphens and embedded
    whitespace control characters (\\t, \\r, \\xa0) collapse to a
    single underscore instead of being silently dropped.
    """
    return normalize_id(name)


def _extract_summary(text: str) -> str:
    """Extract first sentence as summary.

    Args:
        text: Full feature text

    Returns:
        First sentence or first ~100 chars
    """
    # Try to find first sentence (ending with . ! ?)
    match = re.match(r"^([^.!?]+[.!?])", text)
    if match:
        summary = match.group(1).strip()
        # Limit to reasonable length
        if len(summary) <= 150:
            return summary

    # Fallback: first ~100 chars
    if len(text) > 100:
        return text[:97] + "..."

    return text


def _resolve_owners(
    entries: list[dict[str, Any]], source_type: str
) -> list[tuple[str, str | None]]:
    """Assign ``(owner_kind, owner_simple)`` to each accepted feature.

    Algorithm: walk extracted features in PDF order, maintaining a cursor
    over the canonical owner sequence (CLASS_DATA / LINEAGE_DATA). For
    each feature:

    * Build the set of owners whose curated feature list contains this
      ``simple_name``.
    * Prefer the current owner if it matches and hasn't already emitted
      this name; otherwise advance to the next owner in sequence whose
      set contains the name and hasn't yet emitted it.
    * Universal headings absent from every owner (e.g., the per-class
      "Ability Score Improvement" reprints) inherit the current owner.
    * Drop entries whose target slot is already filled (prevents
      duplicate IDs).
    """
    if source_type == "class":
        expected = _build_class_expected_sequence()
        kind = "class"
    elif source_type == "lineage":
        expected = _build_lineage_expected_sequence()
        kind = "lineage"
    else:
        return [(source_type, None) for _ in entries]

    owner_features: dict[str, set[str]] = {}
    owner_order: list[str] = []
    for owner, simple in expected:
        if owner not in owner_features:
            owner_features[owner] = set()
            owner_order.append(owner)
        owner_features[owner].add(simple)

    owner_idx = {o: i for i, o in enumerate(owner_order)}
    emitted: set[tuple[str, str]] = set()
    current_idx = 0
    assigned: list[tuple[str, str | None]] = []

    for entry in entries:
        simple = entry["simple_name"]
        current_owner = owner_order[current_idx]
        matches = [o for o in owner_order if simple in owner_features[o]]

        # Universal features (e.g., per-class "Ability Score Improvement"
        # reprints) are tagged as universal so they always inherit the
        # current owner instead of forcing a cursor jump.
        if simple in _UNIVERSAL_FEATURES:
            if (current_owner, simple) in emitted:
                assigned.append((kind, None))
            else:
                assigned.append((kind, current_owner))
                emitted.add((current_owner, simple))
            continue

        if not matches:
            if (current_owner, simple) in emitted:
                assigned.append((kind, None))
            else:
                assigned.append((kind, current_owner))
                emitted.add((current_owner, simple))
            continue

        if current_owner in matches and (current_owner, simple) not in emitted:
            chosen: str | None = current_owner
        else:
            future = [
                o for o in matches if owner_idx[o] >= current_idx and (o, simple) not in emitted
            ]
            if future:
                chosen = min(future, key=lambda o: owner_idx[o])
            else:
                chosen = None

        if chosen is None:
            assigned.append((kind, None))
            continue

        current_idx = owner_idx[chosen]
        emitted.add((chosen, simple))
        assigned.append((kind, chosen))

    return assigned


# Features that appear in many classes' PDF sections but are not
# consistently listed in CLASS_DATA (e.g., "Ability Score Improvement"
# is only declared in cleric's features list, yet every class section
# in the SRD reprints it). When the resolver encounters one of these
# the current owner is preserved instead of advancing the cursor.
_UNIVERSAL_FEATURES: frozenset[str] = frozenset({"ability_score_improvement"})


def _build_class_expected_sequence() -> list[tuple[str, str]]:
    """Flatten CLASS_DATA into ``[(class_simple, feature_simple), ...]``."""
    ordered = sorted(CLASS_DATA, key=lambda c: c["page"])
    out: list[tuple[str, str]] = []
    for cls in ordered:
        owner = cls["simple_name"]
        for fid in cls.get("features", []):
            simple = fid.split(":", 1)[1] if ":" in fid else fid
            out.append((owner, simple))
    return out


def _build_lineage_expected_sequence() -> list[tuple[str, str]]:
    """Flatten LINEAGE_DATA + subraces into ``[(lineage_simple, name), ...]``.

    Includes implicit section-header traits the PDF emits for every
    lineage block (Ability Score Increase, Age, Alignment, Size, Speed,
    plus the closing Languages). Subraces immediately follow their parent.
    """
    out: list[tuple[str, str]] = []
    ordered = sorted(LINEAGE_DATA, key=lambda lin: lin["page"])
    for lin in ordered:
        out.extend(_lineage_trait_sequence(lin))
        for sub in lin.get("subraces", []):
            out.extend(_lineage_trait_sequence(sub))
    return out


_IMPLICIT_LINEAGE_TRAITS: tuple[str, ...] = (
    "ability_score_increase",
    "age",
    "alignment",
    "size",
    "speed",
)


def _lineage_trait_sequence(entity: dict[str, Any]) -> list[tuple[str, str]]:
    """Flatten a lineage/subrace's trait list into ``(owner, simple)`` pairs."""
    owner = entity["simple_name"]
    out: list[tuple[str, str]] = [(owner, t) for t in _IMPLICIT_LINEAGE_TRAITS]
    for trait in entity.get("traits", []):
        out.append((owner, normalize_id(trait["name"])))
    out.append((owner, "languages"))
    return out
