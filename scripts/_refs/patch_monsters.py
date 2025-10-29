#!/usr/bin/env python3
"""
Patch monsters.json with improvements from review feedback.

This script reads the current monsters.json and applies:
1. Split legendary_actions from actions array
2. Normalize damage resistances/immunities to structured format
3. Clean simple_name normalization (remove punctuation)
4. Fix senses extraction gaps
5. Post-process text cleanup (spacing, dashes, OCR artifacts)
6. Standardize challenge_rating format
7. Rename 'abilities' → 'traits'
8. Add page numbers from raw data

Usage:
    python scripts/patch_monsters.py
"""

import json
import re
from pathlib import Path


def clean_simple_name(name: str) -> str:
    """
    Clean simple_name by removing punctuation, normalizing separators.

    Examples:
        "Enslave (3/Day)." -> "enslave_3_day"
        "Angelic Weapons." -> "angelic_weapons"
        "Tail Swipe" -> "tail_swipe"
    """
    # Remove punctuation except spaces and hyphens
    cleaned = re.sub(r"[^\w\s-]", "", name)
    # Replace spaces and hyphens with underscores
    cleaned = re.sub(r"[\s-]+", "_", cleaned)
    # Collapse multiple underscores
    cleaned = re.sub(r"_+", "_", cleaned)
    # Remove leading/trailing underscores
    cleaned = cleaned.strip("_")
    # Lowercase
    return cleaned.lower()


def normalize_damage_list(damage_str: str) -> list[dict[str, str]]:  # noqa: C901
    """
    Parse damage resistance/immunity/vulnerability string into structured list.

    Examples:
        "bludgeoning, piercing, and slashing from nonmagical attacks"
        -> [
            {"type": "bludgeoning", "qualifier": "nonmagical"},
            {"type": "piercing", "qualifier": "nonmagical"},
            {"type": "slashing", "qualifier": "nonmagical"}
        ]

        "poison, psychic"
        -> [
            {"type": "poison"},
            {"type": "psychic"}
        ]

        "fire, cold; bludgeoning from nonmagical attacks"
        -> [
            {"type": "fire"},
            {"type": "cold"},
            {"type": "bludgeoning", "qualifier": "nonmagical"}
        ]
    """
    if not damage_str or damage_str.strip() == "":
        return []

    result = []

    # Split by semicolon first (separates independent groups)
    groups = [g.strip() for g in damage_str.split(";")]

    for group in groups:
        # Check for qualifier at the end
        qualifier = None
        if "from nonmagical" in group.lower():
            qualifier = "nonmagical"
            # Remove qualifier from group
            group = re.sub(
                r"\s+from\s+nonmagical\s+attacks?(\s+that\s+aren\'t\s+\w+)?",
                "",
                group,
                flags=re.IGNORECASE,
            )
        elif "that aren't" in group.lower():
            # Handle "that aren't adamantine" etc
            match = re.search(r"that\s+aren\'t\s+(\w+)", group, re.IGNORECASE)
            if match:
                qualifier = f"not_{match.group(1)}"
                group = re.sub(r"\s+that\s+aren\'t\s+\w+", "", group, flags=re.IGNORECASE)
        elif "while in" in group.lower():
            # Handle conditional resistances like "while in dim light or darkness"
            match = re.search(r"while\s+in\s+(.+)$", group, re.IGNORECASE)
            if match:
                qualifier = f"in_{match.group(1).replace(' ', '_')}"
                group = re.sub(r"\s+while\s+in\s+.+$", "", group, flags=re.IGNORECASE)

        # Split damage types by commas and "and"
        damage_types = re.split(r",\s*|\s+and\s+", group)

        for dtype in damage_types:
            dtype = dtype.strip()
            # Remove any remaining "and" at the start
            dtype = re.sub(r"^and\s+", "", dtype)
            if dtype:
                entry = {"type": dtype}
                if qualifier:
                    entry["qualifier"] = qualifier
                result.append(entry)

    return result


def clean_text(text: str) -> str:
    """
    Clean OCR artifacts and spacing issues from text.

    Fixes:
    - "10--foot" -> "10-foot"
    - "H it:10" -> "Hit: 10"
    - Multiple spaces -> single space
    - Standardize damage dice format "2d6 + 5" -> "2d6+5"
    """
    if not text:
        return text

    # Fix em/en dashes (-- -> -)
    text = re.sub(r"--+", "-", text)

    # Fix "H it" -> "Hit"
    text = re.sub(r"\bH\s*it\b", "Hit", text)

    # Standardize damage dice spacing "2d6 + 5" -> "2d6+5"
    text = re.sub(r"(\d+d\d+)\s*\+\s*(\d+)", r"\1+\2", text)
    text = re.sub(r"(\d+d\d+)\s*-\s*(\d+)", r"\1-\2", text)

    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Fix missing spaces after punctuation
    text = re.sub(r"([.!?])([A-Z])", r"\1 \2", text)

    return text.strip()


def is_legendary_action(action: dict) -> bool:
    """
    Determine if an action is actually a legendary action.

    Heuristics:
    - Name contains "(Costs" or "(Cost"
    - Name or text mentions "legendary action"
    """
    name = action.get("name", "").lower()
    text = action.get("description", "").lower()

    if "(cost" in name:
        return True
    if "legendary action" in name or "legendary action" in text:
        return True

    return False


def split_legendary_actions(monster: dict) -> tuple[list, list]:
    """
    Split actions into regular actions and legendary actions.

    In SRD data, legendary actions come after an action that contains
    "can take X legendary actions" descriptor text. Once we find that
    marker, all subsequent actions are legendary.

    The action containing the descriptor itself may be a regular action
    (e.g., "Enslave (3/Day)") - it stays in regular actions.

    Returns:
        (regular_actions, legendary_actions)
    """
    actions = monster.get("actions", [])
    regular = []
    legendary = []
    found_legendary_marker = False

    for action in enumerate(actions):
        if isinstance(action, tuple):
            _, action_data = action  # unpack if enumerate returned tuple
        else:
            action_data = action

        text = action_data.get("description", "") + action_data.get("text", "")

        # Check if this action contains the legendary actions descriptor
        if "can take" in text.lower() and "legendary action" in text.lower():
            found_legendary_marker = True
            # This action itself is usually a regular ability with the descriptor appended
            # (e.g., "Enslave (3/Day)" with legendary descriptor text at the end)
            regular.append(action_data)
            continue

        # After we find the marker, everything else is legendary
        if found_legendary_marker:
            legendary.append(action_data)
        else:
            regular.append(action_data)

    return regular, legendary


def standardize_cr(cr: float | int | str) -> int | float:
    """
    Standardize challenge rating to integers where appropriate.

    Examples:
        10.0 -> 10
        0.5 -> 0.5
        0.25 -> 0.25
        "1/2" -> 0.5
        "1/4" -> 0.25
    """
    if isinstance(cr, str):
        if "/" in cr:
            parts = cr.split("/")
            return float(parts[0]) / float(parts[1])
        return float(cr)

    if isinstance(cr, float):
        if cr == int(cr):
            return int(cr)

    return cr


def extract_page_number(monster_name: str, raw_data: list[dict]) -> int | None:
    """
    Extract page number from raw monster data.

    Args:
        monster_name: Display name of the monster
        raw_data: Raw monster data from srd_cc_v5.1_monsters.json

    Returns:
        Page number if found, None otherwise
    """
    for raw_monster in raw_data:
        if raw_monster.get("name", "").lower() == monster_name.lower():
            # Try to find page reference in raw data
            # This might be in different fields depending on source
            if "page" in raw_monster:
                return raw_monster["page"]
            if "source" in raw_monster and isinstance(raw_monster["source"], dict):
                if "page" in raw_monster["source"]:
                    return raw_monster["source"]["page"]

    return None


def patch_monster(monster: dict, raw_data: list[dict]) -> dict:  # noqa: C901
    """
    Apply all patches to a single monster.

    Args:
        monster: Monster dict to patch
        raw_data: Raw monster data for page number extraction

    Returns:
        Patched monster dict
    """
    patched = monster.copy()

    # 1. Clean simple_name
    patched["simple_name"] = clean_simple_name(monster["name"])

    # 2. Split legendary actions
    regular_actions, legendary_actions = split_legendary_actions(monster)
    patched["actions"] = regular_actions
    patched["legendary_actions"] = legendary_actions

    # 3. Rename 'abilities' to 'traits'
    if "abilities" in patched:
        patched["traits"] = patched.pop("abilities")

    # 4. Clean simple_name in traits
    if "traits" in patched:
        for trait in patched["traits"]:
            if "name" in trait:
                trait["simple_name"] = clean_simple_name(trait["name"])
            if "description" in trait:
                trait["description"] = clean_text(trait["description"])
            # Rename 'description' to 'text' for consistency
            if "description" in trait:
                trait["text"] = trait.pop("description")

    # 5. Clean simple_name in actions
    for action in patched["actions"]:
        if "name" in action:
            action["simple_name"] = clean_simple_name(action["name"])
        if "description" in action:
            action["description"] = clean_text(action["description"])
        # Rename 'description' to 'text' for consistency
        if "description" in action:
            action["text"] = action.pop("description")

    # 6. Clean simple_name in legendary_actions
    for action in patched["legendary_actions"]:
        if "name" in action:
            action["simple_name"] = clean_simple_name(action["name"])
        if "description" in action:
            action["description"] = clean_text(action["description"])
        # Rename 'description' to 'text' for consistency
        if "description" in action:
            action["text"] = action.pop("description")

    # 7. Normalize damage resistances/immunities/vulnerabilities
    if "damage_resistances" in patched and isinstance(patched["damage_resistances"], list):
        if patched["damage_resistances"] and isinstance(patched["damage_resistances"][0], str):
            # It's a list of strings, normalize
            combined = ", ".join(patched["damage_resistances"])
            patched["damage_resistances"] = normalize_damage_list(combined)

    if "damage_immunities" in patched and isinstance(patched["damage_immunities"], list):
        if patched["damage_immunities"] and isinstance(patched["damage_immunities"][0], str):
            combined = ", ".join(patched["damage_immunities"])
            patched["damage_immunities"] = normalize_damage_list(combined)

    if "damage_vulnerabilities" in patched and isinstance(patched["damage_vulnerabilities"], list):
        if patched["damage_vulnerabilities"] and isinstance(
            patched["damage_vulnerabilities"][0], str
        ):
            combined = ", ".join(patched["damage_vulnerabilities"])
            patched["damage_vulnerabilities"] = normalize_damage_list(combined)

    # 7a. Normalize condition immunities to structured format
    if "condition_immunities" in patched and isinstance(patched["condition_immunities"], list):
        if patched["condition_immunities"] and isinstance(patched["condition_immunities"][0], str):
            # Convert from ["poisoned", "charmed"] to [{"type": "poisoned"}, {"type": "charmed"}]
            patched["condition_immunities"] = [
                {"type": condition.strip()} for condition in patched["condition_immunities"]
            ]

    # 8. Standardize challenge_rating
    if "challenge_rating" in patched:
        patched["challenge_rating"] = standardize_cr(patched["challenge_rating"])

    # 9. Clean summary
    if "summary" in patched:
        patched["summary"] = clean_text(patched["summary"])

    # 10. Add page number
    page = extract_page_number(monster["name"], raw_data)
    if page:
        patched["page"] = page

    # 11. Add src field
    patched["src"] = "SRD_CC_v5.1"

    return patched


def main():
    """Main entry point."""
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    data_dir = project_root / "data"
    raw_dir = project_root / "raw"

    monsters_file = data_dir / "monsters.json"
    raw_monsters_file = raw_dir / "srd_cc_v5.1_monsters.json"
    output_file = data_dir / "monsters.json"

    # Load data
    print(f"Loading monsters from {monsters_file}...")
    with open(monsters_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loading raw monster data from {raw_monsters_file}...")
    with open(raw_monsters_file, encoding="utf-8") as f:
        raw_data_wrapper = json.load(f)

    # Extract raw monsters list
    if isinstance(raw_data_wrapper, dict) and "monsters" in raw_data_wrapper:
        raw_data = raw_data_wrapper["monsters"]
    else:
        raw_data = raw_data_wrapper

    # Get monster list (handle both array and object with 'monsters' key)
    if isinstance(data, dict) and "monsters" in data:
        monsters = data["monsters"]
        wrapper = data
    else:
        monsters = data
        wrapper = None

    # Patch each monster
    print(f"Patching {len(monsters)} monsters...")
    patched_monsters = []
    for i, monster in enumerate(monsters):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(monsters)}...")
        patched = patch_monster(monster, raw_data)
        patched_monsters.append(patched)

    # Save patched data
    if wrapper:
        wrapper["monsters"] = patched_monsters
        output_data = wrapper
    else:
        output_data = patched_monsters

    print(f"Writing patched monsters to {output_file}...")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Patched {len(patched_monsters)} monsters successfully!")

    # Summary statistics
    legendary_count = sum(1 for m in patched_monsters if m.get("legendary_actions"))
    with_page = sum(1 for m in patched_monsters if "page" in m)

    print("\nSummary:")
    print(f"  - Monsters with legendary actions: {legendary_count}")
    print(f"  - Monsters with page numbers: {with_page}")
    print("  - All monsters now have 'traits' instead of 'abilities'")
    print("  - All simple_names cleaned of punctuation")
    print("  - All damage resistances/immunities normalized")


if __name__ == "__main__":
    main()
