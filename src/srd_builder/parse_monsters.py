#!/usr/bin/env python3
"""
SRD 5.1 Monster Normalization Script

Reads: raw/srd_cc_v5.1_monsters.json
Writes: data/monsters.json

Changes:
- Add simple_name (normalized ID)
- Add summary (one-sentence description)
- Parse ability scores to integers
- Parse armor class to integer
- Parse hit points to integer
- Parse speed to structured format
- Parse saving throws to dict
- Parse skills to dict
- Parse challenge rating and XP value
- Normalize action damage/to_hit
- Add three-level naming to abilities/actions
"""

import json
import re
from pathlib import Path


def normalize_string_to_id(name: str) -> str:
    """Convert name to simple_name ID format.

    Examples:
        "Aboleth" -> "aboleth"
        "Ancient Red Dragon" -> "ancient_red_dragon"
        "Gelatinous Cube" -> "gelatinous_cube"
    """
    return name.lower().replace(" ", "_").replace("-", "_")


def generate_summary(monster: dict) -> str:
    """Generate one-sentence summary from monster data.

    Priority:
    1. Use first ability description (usually most characteristic)
    2. Use first action description
    3. Use generic template
    """
    # Try first ability
    if monster.get("abilities") and len(monster["abilities"]) > 0:
        first_ability = monster["abilities"][0]
        desc = first_ability.get("description", "")
        # Take first sentence
        first_sentence = desc.split(".")[0] + "." if "." in desc else desc
        if len(first_sentence) < 200:
            return first_sentence

    # Try first action
    if monster.get("actions") and len(monster["actions"]) > 0:
        first_action = monster["actions"][0]
        desc = first_action.get("description", "")
        # Take first sentence
        first_sentence = desc.split(".")[0] + "." if "." in desc else desc
        if len(first_sentence) < 200:
            return first_sentence

    # Generic template
    return f"A {monster['size'].lower()} {monster['type']} with CR {parse_challenge_rating(monster['challenge'])[0]}"


def parse_armor_class(ac_str: str) -> int:
    """Parse armor class from string.

    Examples:
        "17 (natural armor)" -> 17
        "15" -> 15
        "10 in humanoid form, 11 in bear form" -> 10 (use first value)
    """
    # Handle multiple AC values (take first)
    if "," in ac_str:
        ac_str = ac_str.split(",")[0]

    # Remove parenthetical descriptions
    ac_str = ac_str.split("(")[0].strip()

    # Extract first number
    match = re.search(r"\d+", ac_str)
    if match:
        return int(match.group())

    return 10  # Default AC if can't parse


def parse_hit_points(hp_str: str) -> tuple[int, str]:
    """Parse hit points and hit dice.

    Examples:
        "135 (18d10 + 36)" -> (135, "18d10 + 36")
        "45" -> (45, "")
    """
    if "(" in hp_str:
        hp, dice = hp_str.split("(")
        return int(hp.strip()), dice.strip(")")
    return int(hp_str.strip()), ""


def parse_speed(speed_str: str) -> dict[str, int]:
    """Parse speed string to structured format.

    Examples:
        "10 ft., swim 40 ft." -> {"walk": 10, "swim": 40}
        "30 ft., fly 90 ft." -> {"walk": 30, "fly": 90}
        "40 ft." -> {"walk": 40}
        "burrow 40ft., swim 40 ft." -> {"burrow": 40, "swim": 40}
    """
    speeds = {}

    # Use regex to find all speed patterns
    # Matches: "40 ft." or "swim 40 ft." or "fly 60ft."
    pattern = r"(?:(\w+)\s+)?(\d+)\s*ft"
    matches = re.findall(pattern, speed_str)

    for match in matches:
        speed_type, speed_value = match
        if not speed_type:
            # No type specified, assume walk
            speed_type = "walk"
        speeds[speed_type] = int(speed_value)

    return speeds if speeds else {"walk": 0}


def parse_ability_scores(stats: dict) -> dict[str, int]:
    """Parse ability scores from string to int.

    Input: {"str": "21", "dex": "9", ...}
    OR: {"str": "29(+9)", "dex": "10", ...}  (with modifier)
    Output: {"strength": 21, "dexterity": 9, ...}
    """
    ability_map = {
        "str": "strength",
        "dex": "dexterity",
        "con": "constitution",
        "int": "intelligence",
        "wis": "wisdom",
        "cha": "charisma",
    }

    result = {}
    for key, value in stats.items():
        # Handle "29(+9)" format - extract just the score
        if "(" in str(value):
            value = str(value).split("(")[0]
        result[ability_map[key]] = int(value)

    return result


def parse_proficiencies(prof_str: str) -> dict[str, int]:
    """Parse saving throws or skills string to dict.

    Examples:
        "Con +6, Int +8, Wis +6" -> {"constitution": 6, "intelligence": 8, "wisdom": 6}
        "History +12, Perception +10" -> {"history": 12, "perception": 10}
    """
    if not prof_str:
        return {}

    profs = {}
    parts = prof_str.split(",")

    for part in parts:
        part = part.strip()
        # Match "Con +6" or "History +12"
        match = re.match(r"(\w+)\s+([+-]\d+)", part)
        if match:
            ability_or_skill = match.group(1).lower()
            bonus = int(match.group(2))

            # Normalize ability names
            ability_map = {
                "str": "strength",
                "dex": "dexterity",
                "con": "constitution",
                "int": "intelligence",
                "wis": "wisdom",
                "cha": "charisma",
            }

            if ability_or_skill in ability_map:
                profs[ability_map[ability_or_skill]] = bonus
            else:
                profs[ability_or_skill] = bonus

    return profs


def parse_challenge_rating(cr_str: str) -> tuple[float, int]:
    """Parse challenge rating and XP value.

    Examples:
        "10 (5,900 XP)" -> (10.0, 5900)
        "1/2 (100 XP)" -> (0.5, 100)
        "1/4 (50 XP)" -> (0.25, 50)
    """
    # Match "10 (5,900 XP)" or "1/2 (100 XP)"
    match = re.match(r"([\d/]+)\s+\(([,\d]+)\s+XP\)", cr_str)
    if match:
        cr_part = match.group(1)
        xp_part = match.group(2).replace(",", "")

        # Handle fractions
        if "/" in cr_part:
            num, denom = cr_part.split("/")
            cr = int(num) / int(denom)
        else:
            cr = float(cr_part)

        return cr, int(xp_part)

    return 0.0, 0


def normalize_ability(ability: dict) -> dict:
    """Add three-level naming to ability."""
    return {
        "simple_name": normalize_string_to_id(ability["name"]),
        "name": ability["name"],
        "description": ability["description"],
    }


def normalize_action(action: dict) -> dict:
    """Add three-level naming and parse action data."""
    normalized = {
        "simple_name": normalize_string_to_id(action["name"]),
        "name": action["name"],
        "description": action["description"],
    }

    # Add optional fields if present
    if "damage_type" in action:
        normalized["damage_type"] = action["damage_type"]
    if "damage_dice" in action:
        normalized["damage_dice"] = action["damage_dice"]
    if "to_hit" in action:
        normalized["to_hit"] = int(action["to_hit"].replace("+", ""))
    if "reach" in action:
        reach_match = re.match(r"(\d+)", action["reach"])
        if reach_match:
            normalized["reach"] = int(reach_match.group(1))
    if "saving_throw" in action:
        normalized["saving_throw"] = action["saving_throw"]

    return normalized


def parse_senses(senses_str: str) -> dict:
    """Parse senses string to structured format.

    Examples:
        "darkvision 120 ft., passive Perception 20" ->
        {
            "darkvision": 120,
            "passive_perception": 20
        }
    """
    parsed = {}
    parts = senses_str.split(",")

    for part in parts:
        part = part.strip()

        # Match "darkvision 120 ft."
        if "darkvision" in part.lower():
            match = re.search(r"(\d+)", part)
            if match:
                parsed["darkvision"] = int(match.group(1))

        # Match "passive Perception 20"
        if "passive perception" in part.lower():
            match = re.search(r"(\d+)", part)
            if match:
                parsed["passive_perception"] = int(match.group(1))

    return parsed


def normalize_monster(monster: dict) -> dict:
    """Normalize a single monster to our format."""

    # Parse basic fields
    simple_name = normalize_string_to_id(monster["name"])
    summary = generate_summary(monster)
    ac = parse_armor_class(monster["armor_class"])
    hp, hit_dice = parse_hit_points(monster["hit_points"])
    speed = parse_speed(monster["speed"])
    ability_scores = parse_ability_scores(monster["stats"])
    cr, xp = parse_challenge_rating(monster["challenge"])
    senses = parse_senses(monster.get("senses", ""))

    # Parse proficiencies
    saving_throws = parse_proficiencies(monster.get("saving_throws", ""))
    skills = parse_proficiencies(monster.get("skills", ""))

    # Normalize abilities and actions
    abilities = [normalize_ability(a) for a in monster.get("abilities", [])]
    actions = [normalize_action(a) for a in monster.get("actions", [])]

    # Parse resistances/immunities
    damage_resistances = (
        monster.get("damage_resistances", "").split(";")
        if monster.get("damage_resistances")
        else []
    )
    damage_immunities = (
        monster.get("damage_immunities", "").split(";") if monster.get("damage_immunities") else []
    )
    condition_immunities = (
        monster.get("condition_immunities", "").split(",")
        if monster.get("condition_immunities")
        else []
    )

    # Clean up lists
    damage_resistances = [r.strip() for r in damage_resistances if r.strip()]
    damage_immunities = [i.strip() for i in damage_immunities if i.strip()]
    condition_immunities = [c.strip() for c in condition_immunities if c.strip()]

    return {
        # Identity (four-level naming with namespaced ID)
        "id": f"monster:{simple_name}",
        "simple_name": simple_name,
        "name": monster["name"],
        "summary": summary,
        # Basic Stats
        "size": monster["size"],
        "type": monster["type"],
        "alignment": monster.get("alignment", "unaligned"),
        # Combat Stats
        "armor_class": ac,
        "hit_points": hp,
        "hit_dice": hit_dice,
        "speed": speed,
        # Ability Scores
        "ability_scores": ability_scores,
        # Proficiencies
        "saving_throws": saving_throws,
        "skills": skills,
        # Abilities & Actions
        "abilities": abilities,
        "actions": actions,
        # Challenge
        "challenge_rating": cr,
        "xp_value": xp,
        # Senses
        "senses": senses,
        # Resistances/Immunities
        "damage_resistances": damage_resistances,
        "damage_immunities": damage_immunities,
        "condition_immunities": condition_immunities,
    }


def main():
    """Main extraction process."""
    # Paths
    project_root = Path(__file__).parent.parent
    raw_file = project_root / "raw" / "srd_cc_v5.1_monsters.json"
    output_file = project_root / "data" / "monsters.json"

    print(f"Reading raw monsters from: {raw_file}")

    # Load raw data
    with open(raw_file) as f:
        raw_data = json.load(f)

    print(f"Found {len(raw_data['monsters'])} monsters")

    # Normalize all monsters
    normalized_monsters = []
    for monster in raw_data["monsters"]:
        try:
            normalized = normalize_monster(monster)
            normalized_monsters.append(normalized)
        except Exception as e:
            print(f"ERROR normalizing {monster['name']}: {e}")
            raise

    # Build output
    output = {
        "version": "5.1",
        "source": "SRD_CC_v5.1",
        "count": len(normalized_monsters),
        "monsters": normalized_monsters,
    }

    # Write output
    print(f"Writing {len(normalized_monsters)} normalized monsters to: {output_file}")
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)

    print("✅ Monster normalization complete!")
    print(f"   Total monsters: {len(normalized_monsters)}")
    print(f"   Output: {output_file}")


if __name__ == "__main__":
    main()
