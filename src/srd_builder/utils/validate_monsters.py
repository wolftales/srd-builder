"""
Validate extracted monster data for completeness and correctness.

This module provides validation functions to ensure monster extraction
is complete by checking for expected monster categories and counts.
"""

from collections import Counter
from typing import Any

# Expected monster categories with known members
EXPECTED_CATEGORIES = {
    "Dragons (chromatic)": [
        "Black Dragon",
        "Blue Dragon",
        "Green Dragon",
        "Red Dragon",
        "White Dragon",
    ],
    "Dragons (metallic)": [
        "Brass Dragon",
        "Bronze Dragon",
        "Copper Dragon",
        "Gold Dragon",
        "Silver Dragon",
    ],
    "Giants": [
        "Cloud Giant",
        "Fire Giant",
        "Frost Giant",
        "Hill Giant",
        "Stone Giant",
        "Storm Giant",
    ],
    "Elementals": ["Air Elemental", "Earth Elemental", "Fire Elemental", "Water Elemental"],
    "Demons": ["Balor", "Glabrezu", "Hezrou", "Marilith", "Nalfeshnee", "Vrock"],
    "Devils": [
        "Barbed Devil",
        "Bearded Devil",
        "Bone Devil",
        "Erinyes",
        "Horned Devil",
        "Ice Devil",
        "Pit Fiend",
    ],
    "Lycanthropes": ["Werewolf", "Wereboar", "Werebear", "Wererat", "Weretiger"],
    "Undead": ["Zombie", "Skeleton", "Ghost", "Vampire", "Lich", "Mummy"],
}

# Expected minimum counts for validation
EXPECTED_MIN_MONSTERS = 290  # Should be around 296
EXPECTED_MAX_MONSTERS = 320  # Upper bound (reference was 319 but inflated)


def validate_category_completeness(monsters: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """
    Validate that all expected monster categories are present.

    Args:
        monsters: List of monster dicts, each with at least a 'name' field

    Returns:
        Dict with category validation results:
        {
            'category_name': {
                'expected': 6,
                'found': 6,
                'missing': [],
                'complete': True
            }
        }
    """
    names = [m["name"] for m in monsters]
    results = {}

    for category, expected in EXPECTED_CATEGORIES.items():
        found = [e for e in expected if any(e in n for n in names)]
        missing = [e for e in expected if not any(e in n for n in names)]

        results[category] = {
            "expected": len(expected),
            "found": len(found),
            "missing": missing,
            "complete": len(missing) == 0,
        }

    return results


def validate_monster_count(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Validate total monster count is in expected range.

    Args:
        monsters: List of monster dicts

    Returns:
        Dict with count validation results
    """
    count = len(monsters)
    in_range = EXPECTED_MIN_MONSTERS <= count <= EXPECTED_MAX_MONSTERS

    return {
        "count": count,
        "min_expected": EXPECTED_MIN_MONSTERS,
        "max_expected": EXPECTED_MAX_MONSTERS,
        "in_range": in_range,
    }


def validate_uniqueness(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Validate that all monster names are unique (no duplicates).

    Args:
        monsters: List of monster dicts with 'name' field

    Returns:
        Dict with uniqueness validation results
    """
    names = [m["name"] for m in monsters]
    counter = Counter(names)
    duplicates = {name: count for name, count in counter.items() if count > 1}

    return {
        "total": len(names),
        "unique": len(counter),
        "duplicates": duplicates,
        "all_unique": len(duplicates) == 0,
    }


def validate_alphabetic_coverage(monsters: list[dict[str, Any]]) -> dict[str, int]:
    """
    Check alphabetic distribution of monsters (helps spot missing sections).

    Args:
        monsters: List of monster dicts with 'name' field

    Returns:
        Dict mapping first letter to count
    """
    names = [m["name"] for m in monsters]
    first_letters = Counter(n[0].upper() for n in names if n)
    return dict(sorted(first_letters.items()))


def validate_all(monsters: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Run all validation checks on extracted monsters.

    Args:
        monsters: List of monster dicts

    Returns:
        Dict with all validation results and overall pass/fail
    """
    categories = validate_category_completeness(monsters)
    count = validate_monster_count(monsters)
    uniqueness = validate_uniqueness(monsters)
    alphabetic = validate_alphabetic_coverage(monsters)

    # Overall pass: categories complete, count in range, all unique
    categories_pass = all(c["complete"] for c in categories.values())
    overall_pass = categories_pass and count["in_range"] and uniqueness["all_unique"]

    return {
        "pass": overall_pass,
        "categories": categories,
        "count": count,
        "uniqueness": uniqueness,
        "alphabetic": alphabetic,
    }


def print_validation_report(results: dict[str, Any]) -> None:
    """Print a human-readable validation report."""
    print("=" * 60)
    print("MONSTER EXTRACTION VALIDATION REPORT")
    print("=" * 60)

    # Overall result
    status = "✓ PASS" if results["pass"] else "✗ FAIL"
    print(f"\nOverall: {status}\n")

    # Count validation
    count = results["count"]
    print(f"Monster Count: {count['count']}")
    print(f"  Expected range: {count['min_expected']}-{count['max_expected']}")
    print(f"  Status: {'✓' if count['in_range'] else '✗'}\n")

    # Uniqueness
    uniq = results["uniqueness"]
    print(f"Uniqueness: {uniq['unique']}/{uniq['total']} unique")
    if uniq["duplicates"]:
        print("  ✗ Duplicates found:")
        for name, cnt in uniq["duplicates"].items():
            print(f"    {name}: {cnt}x")
    else:
        print("  ✓ All unique\n")

    # Category completeness
    print("Category Completeness:")
    for category, data in results["categories"].items():
        status = "✓" if data["complete"] else "✗"
        print(f"  {status} {category}: {data['found']}/{data['expected']}")
        if data["missing"]:
            print(f"      Missing: {', '.join(data['missing'])}")

    # Alphabetic distribution
    print("\nAlphabetic Distribution:")
    alpha = results["alphabetic"]
    for letter, count in alpha.items():
        bar = "█" * (count // 2)  # Simple bar chart
        print(f"  {letter}: {count:3d} {bar}")

    print("\n" + "=" * 60)
