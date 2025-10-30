#!/usr/bin/env python3
"""Generate a coverage report showing expected vs actual parsed fields."""

import json
import sys
from pathlib import Path


def count_expected_from_raw(raw_path: Path) -> dict[str, int]:  # noqa: C901
    """Count expected fields by analyzing raw PDF extraction."""
    with open(raw_path) as f:
        data = json.load(f)

    expected = {}
    total_monsters = len(data["monsters"])

    # Define label detection rules: (field_name, check_function, min_size, max_size)
    labels_to_check = [
        ("legendary", lambda t: "legendary" in t and "action" in t, 10.0, 11.0),
        (
            "saving_throws",
            lambda t: "saving" in t and "throw" in t,
            9.5,
            10.0,
        ),
        ("skills", lambda t: t == "skills", 9.5, 10.0),
        (
            "damage_res",
            lambda t: "damage" in t and "resistance" in t,
            9.5,
            10.0,
        ),
        (
            "damage_imm",
            lambda t: "damage" in t and "immunit" in t,
            9.5,
            10.0,
        ),
        (
            "damage_vul",
            lambda t: "damage" in t and "vulnerab" in t,
            9.5,
            10.0,
        ),
        (
            "cond_imm",
            lambda t: "condition" in t and "immunit" in t,
            9.5,
            10.0,
        ),
    ]

    for label_name, check_fn, min_size, max_size in labels_to_check:
        count = 0
        for monster in data["monsters"]:
            blocks = monster.get("blocks", [])
            for block in blocks:
                text = " ".join(block.get("text", "").split()).strip().lower()
                font = block.get("font", "")
                size = block.get("size", 0)

                if "bold" in font.lower() and min_size <= size <= max_size:
                    if check_fn(text):
                        count += 1
                        break
        expected[label_name] = count

    # Core fields that should be 100%
    for field in [
        "name",
        "armor_class",
        "hit_points",
        "speed",
        "ability_scores",
        "senses",
        "languages",
        "cr",
    ]:
        expected[field] = total_monsters

    # Traits: BoldItalic entries before Actions header
    traits_count = 0
    actions_count = 0
    for monster in data["monsters"]:
        blocks = monster.get("blocks", [])

        # Find Actions header
        actions_idx = None
        for i, block in enumerate(blocks):
            text = " ".join(block.get("text", "").split()).strip()
            if text == "Actions" and block.get("size", 0) >= 10.8:
                actions_idx = i
                actions_count += 1  # Monster has Actions section
                break

        # Check for BoldItalic traits before Actions
        if actions_idx is not None:
            for i in range(actions_idx):
                block = blocks[i]
                if (
                    block.get("font") == "Calibri-BoldItalic"
                    and block.get("size") == 9.84
                    and block.get("text", "").strip().endswith(".")
                ):
                    traits_count += 1
                    break

    expected["traits"] = traits_count
    expected["actions"] = actions_count

    return expected


def count_actual_from_parsed(parsed_path: Path) -> tuple[dict[str, int], int]:
    """Count actual parsed fields from monsters.json."""
    with open(parsed_path) as f:
        data = json.load(f)

    items = data.get("items", [])
    total = len(items)

    actual = {
        "name": sum(1 for m in items if m.get("name")),
        "armor_class": sum(1 for m in items if m.get("armor_class") and m.get("armor_class") != 0),
        "hit_points": sum(1 for m in items if m.get("hit_points") and m.get("hit_points") != 0),
        "speed": sum(1 for m in items if m.get("speed")),
        "ability_scores": sum(1 for m in items if m.get("ability_scores")),
        "saving_throws": sum(
            1 for m in items if m.get("saving_throws") and len(m.get("saving_throws", [])) > 0
        ),
        "skills": sum(1 for m in items if m.get("skills") and len(m.get("skills", [])) > 0),
        "damage_res": sum(
            1
            for m in items
            if m.get("damage_resistances") and len(m.get("damage_resistances", [])) > 0
        ),
        "damage_imm": sum(
            1
            for m in items
            if m.get("damage_immunities") and len(m.get("damage_immunities", [])) > 0
        ),
        "damage_vul": sum(
            1
            for m in items
            if m.get("damage_vulnerabilities") and len(m.get("damage_vulnerabilities", [])) > 0
        ),
        "cond_imm": sum(
            1
            for m in items
            if m.get("condition_immunities") and len(m.get("condition_immunities", [])) > 0
        ),
        "senses": sum(1 for m in items if m.get("senses")),
        "languages": sum(1 for m in items if m.get("languages")),
        "cr": sum(1 for m in items if m.get("challenge_rating") is not None),
        "traits": sum(1 for m in items if m.get("traits") and len(m.get("traits", [])) > 0),
        "actions": sum(1 for m in items if m.get("actions") and len(m.get("actions", [])) > 0),
        "legendary": sum(
            1
            for m in items
            if m.get("legendary_actions") and len(m.get("legendary_actions", [])) > 0
        ),
    }

    return actual, total


def main():
    # Paths
    raw_path = Path("rulesets/srd_5_1/raw/monsters_raw.json")
    parsed_path = Path("dist/srd_5_1/data/monsters.json")

    if not raw_path.exists():
        print(f"Error: {raw_path} not found", file=sys.stderr)
        sys.exit(1)

    if not parsed_path.exists():
        print(f"Error: {parsed_path} not found", file=sys.stderr)
        sys.exit(1)

    # Get counts
    expected = count_expected_from_raw(raw_path)
    actual, total = count_actual_from_parsed(parsed_path)

    # Print report
    print(f"Parser Coverage Report ({total} monsters)")
    print("=" * 80)
    print()
    print(f"{'Field':<20} {'Actual':>7} {'Expected':>9} {'Percent':>8} {'Status':>10}")
    print("━" * 80)

    # Field order and display names
    fields = [
        ("name", "Name"),
        ("armor_class", "Armor Class"),
        ("hit_points", "Hit Points"),
        ("speed", "Speed"),
        ("ability_scores", "Ability Scores"),
        ("saving_throws", "Saving Throws"),
        ("skills", "Skills"),
        ("damage_res", "Damage Resist"),
        ("damage_imm", "Damage Immune"),
        ("damage_vul", "Damage Vuln"),
        ("cond_imm", "Condition Immune"),
        ("senses", "Senses"),
        ("languages", "Languages"),
        ("cr", "Challenge Rating"),
        ("traits", "Traits"),
        ("actions", "Actions"),
        ("legendary", "Legendary Actions"),
    ]

    for field_key, field_name in fields:
        actual_count = actual.get(field_key, 0)
        expected_count = expected.get(field_key, total)

        if expected_count > 0:
            percent = (actual_count * 100) // expected_count
        else:
            percent = 0

        # Status indicator
        if percent >= 100:
            status = "✓ Complete"
        elif percent >= 90:
            status = "✓ Excellent"
        elif percent >= 75:
            status = "△ Good"
        elif percent >= 50:
            status = "△ Partial"
        else:
            status = "✗ Low"

        print(f"{field_name:<20} {actual_count:>7} {expected_count:>9} {percent:>7}% {status:>10}")

    print()
    print("Note: 'Expected' counts are based on labels found in raw PDF extraction.")
    print("      Some fields (traits, actions) may show <100% if monsters lack those sections.")


if __name__ == "__main__":
    main()
