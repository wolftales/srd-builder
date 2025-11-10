"""Parse extracted feature data into structured feature records.

Pure parsing module (no I/O) - takes raw feature data and returns
structured feature records matching the feature schema.
"""

from __future__ import annotations

import re
from typing import Any


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
    features = []

    for raw in raw_features.get("features", []):
        name = raw["name"]
        text = raw["text"]
        page = raw["page"]

        # Skip if no meaningful text
        if len(text) < 20:
            continue

        # Skip section headers (not actual features)
        if _is_section_header(name):
            continue

        # Create simple_name (lowercase, underscored)
        simple_name = _create_simple_name(name)

        # Build feature record
        feature = {
            "id": f"feature:{simple_name}",
            "name": name,
            "simple_name": simple_name,
            "page": page,
            "source": raw_features.get("source", "SRD 5.1"),
            "text": text,
        }

        # Extract summary (first sentence)
        summary = _extract_summary(text)
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

    Args:
        name: Feature name

    Returns:
        Lowercase underscored simple_name
    """
    # Remove punctuation, lowercase, replace spaces with underscores
    simple = re.sub(r"[^\w\s]", "", name)
    simple = simple.lower().replace(" ", "_")

    # Remove trailing/leading underscores
    simple = simple.strip("_")

    return simple


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
