"""
Tests for monster validation functions.
"""

import pytest

from srd_builder.validate_monsters import (
    validate_all,
    validate_alphabetic_coverage,
    validate_category_completeness,
    validate_monster_count,
    validate_uniqueness,
)


@pytest.fixture
def sample_monsters():
    """
    Complete sample monster data including all validation category members.
    This ensures tests validate against the full expected set.
    """
    return [
        # Dragons (chromatic) - 5
        {"name": "Ancient Black Dragon"},
        {"name": "Ancient Blue Dragon"},
        {"name": "Ancient Green Dragon"},
        {"name": "Ancient Red Dragon"},
        {"name": "Ancient White Dragon"},
        # Dragons (metallic) - 5
        {"name": "Ancient Brass Dragon"},
        {"name": "Ancient Bronze Dragon"},
        {"name": "Ancient Copper Dragon"},
        {"name": "Ancient Gold Dragon"},
        {"name": "Ancient Silver Dragon"},
        # Giants - 6
        {"name": "Cloud Giant"},
        {"name": "Fire Giant"},
        {"name": "Frost Giant"},
        {"name": "Hill Giant"},
        {"name": "Stone Giant"},
        {"name": "Storm Giant"},
        # Elementals - 4
        {"name": "Air Elemental"},
        {"name": "Earth Elemental"},
        {"name": "Fire Elemental"},
        {"name": "Water Elemental"},
        # Demons - 6
        {"name": "Balor"},
        {"name": "Glabrezu"},
        {"name": "Hezrou"},
        {"name": "Marilith"},
        {"name": "Nalfeshnee"},
        {"name": "Vrock"},
        # Devils - 7
        {"name": "Barbed Devil"},
        {"name": "Bearded Devil"},
        {"name": "Bone Devil"},
        {"name": "Erinyes"},
        {"name": "Horned Devil"},
        {"name": "Ice Devil"},
        {"name": "Pit Fiend"},
        # Lycanthropes - 5
        {"name": "Werewolf"},
        {"name": "Wereboar"},
        {"name": "Werebear"},
        {"name": "Wererat"},
        {"name": "Weretiger"},
        # Undead - 6
        {"name": "Zombie"},
        {"name": "Skeleton"},
        {"name": "Ghost"},
        {"name": "Vampire"},
        {"name": "Lich"},
        {"name": "Mummy"},
    ]


def test_validate_category_completeness_all_present(sample_monsters):
    """Test category validation when all expected monsters are present."""
    results = validate_category_completeness(sample_monsters)

    # Check that some categories pass
    assert results["Giants"]["complete"] is True
    assert results["Giants"]["found"] == 6
    assert results["Giants"]["missing"] == []

    assert results["Elementals"]["complete"] is True
    assert results["Lycanthropes"]["complete"] is True


def test_validate_category_completeness_missing_monsters():
    """Test category validation when some monsters are missing."""
    incomplete = [
        {"name": "Cloud Giant"},
        {"name": "Fire Giant"},
        # Missing 4 giants
    ]

    results = validate_category_completeness(incomplete)
    assert results["Giants"]["complete"] is False
    assert results["Giants"]["found"] == 2
    assert len(results["Giants"]["missing"]) == 4


def test_validate_monster_count_in_range():
    """Test count validation with count in expected range."""
    # 295 monsters should be in range (290-320)
    monsters = [{"name": f"Monster {i}"} for i in range(295)]
    result = validate_monster_count(monsters)

    assert result["count"] == 295
    assert result["in_range"] is True


def test_validate_monster_count_out_of_range():
    """Test count validation with count out of range."""
    # 100 monsters should be out of range
    monsters = [{"name": f"Monster {i}"} for i in range(100)]
    result = validate_monster_count(monsters)

    assert result["count"] == 100
    assert result["in_range"] is False


def test_validate_uniqueness_all_unique():
    """Test uniqueness validation with all unique names."""
    monsters = [
        {"name": "Dragon"},
        {"name": "Giant"},
        {"name": "Goblin"},
    ]
    result = validate_uniqueness(monsters)

    assert result["all_unique"] is True
    assert result["total"] == 3
    assert result["unique"] == 3
    assert result["duplicates"] == {}


def test_validate_uniqueness_with_duplicates():
    """Test uniqueness validation with duplicate names."""
    monsters = [
        {"name": "Dragon"},
        {"name": "Dragon"},
        {"name": "Giant"},
    ]
    result = validate_uniqueness(monsters)

    assert result["all_unique"] is False
    assert result["total"] == 3
    assert result["unique"] == 2
    assert result["duplicates"] == {"Dragon": 2}


def test_validate_alphabetic_coverage():
    """Test alphabetic distribution counting."""
    monsters = [
        {"name": "Ancient Dragon"},
        {"name": "Adult Dragon"},
        {"name": "Bear"},
        {"name": "Giant"},
    ]
    result = validate_alphabetic_coverage(monsters)

    assert result["A"] == 2
    assert result["B"] == 1
    assert result["G"] == 1


def test_validate_all_pass(sample_monsters):
    """Test full validation with good data."""
    # sample_monsters has all 44 validation category members
    # Need more to pass count check: 44 + 252 = 296
    full_monsters = sample_monsters + [{"name": f"Test Monster {i}"} for i in range(252)]

    results = validate_all(full_monsters)
    assert results["pass"] is True
    assert results["count"]["in_range"] is True
    assert results["uniqueness"]["all_unique"] is True


def test_validate_all_fail_on_duplicates():
    """Test full validation fails with duplicates."""
    monsters = [
        {"name": "Dragon"},
        {"name": "Dragon"},
    ] + [
        {"name": f"Monster {i}"} for i in range(294)
    ]  # Total 296

    results = validate_all(monsters)
    assert results["pass"] is False
    assert results["uniqueness"]["all_unique"] is False


def test_validate_all_fail_on_count():
    """Test full validation fails with wrong count."""
    monsters = [{"name": f"Monster {i}"} for i in range(50)]  # Too few

    results = validate_all(monsters)
    assert results["pass"] is False
    assert results["count"]["in_range"] is False
