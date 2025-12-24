"""Tests for cross-reference validation."""

from srd_builder.validate_references import ReferenceValidator


def test_valid_damage_type_refs():
    """Valid damage type references pass validation."""
    datasets = {
        "damage_types": {"items": [{"id": "damage:fire"}]},
        "monsters": {"items": []},
        "spells": {
            "items": [
                {
                    "id": "spell:fireball",
                    "effects": {
                        "damage": {"type_id": "fire", "dice": "8d6"}  # Short format
                    },
                }
            ]
        },
        "equipment": {"items": []},
        "magic_items": {"items": []},
        "tables": {"items": []},
        "lineages": {"items": []},
        "classes": {"items": []},
        "ability_scores": {"items": []},
        "skills": {"items": []},
        "weapon_properties": {"items": []},
        "conditions": {"items": []},
        "diseases": {"items": []},
        "poisons": {"items": []},
        "features": {"features": []},
        "rules": {"items": []},
    }

    validator = ReferenceValidator(datasets)
    validator.validate_damage_type_refs()
    assert len(validator.errors) == 0


def test_invalid_damage_type_refs():
    """Invalid damage type references fail validation."""
    datasets = {
        "damage_types": {"items": [{"id": "damage:fire"}]},
        "monsters": {"items": []},
        "spells": {
            "items": [
                {
                    "id": "spell:icestorm",
                    "effects": {
                        "damage": {"type_id": "cold", "dice": "4d8"}  # Not in damage_types
                    },
                }
            ]
        },
        "equipment": {"items": []},
        "magic_items": {"items": []},
        "tables": {"items": []},
        "lineages": {"items": []},
        "classes": {"items": []},
        "ability_scores": {"items": []},
        "skills": {"items": []},
        "weapon_properties": {"items": []},
        "conditions": {"items": []},
        "diseases": {"items": []},
        "poisons": {"items": []},
        "features": {"features": []},
        "rules": {"items": []},
    }

    validator = ReferenceValidator(datasets)
    validator.validate_damage_type_refs()
    assert len(validator.errors) == 1
    assert "cold" in validator.errors[0]


def test_backward_compat_full_id():
    """Full ID format (damage:fire) works."""
    datasets = {
        "damage_types": {"items": [{"id": "damage:fire"}]},
        "monsters": {"items": []},
        "spells": {
            "items": [
                {
                    "id": "spell:fireball",
                    "effects": {
                        "damage": {"type_id": "damage:fire", "dice": "8d6"}  # Full format
                    },
                }
            ]
        },
        "equipment": {"items": []},
        "magic_items": {"items": []},
        "tables": {"items": []},
        "lineages": {"items": []},
        "classes": {"items": []},
        "ability_scores": {"items": []},
        "skills": {"items": []},
        "weapon_properties": {"items": []},
        "conditions": {"items": []},
        "diseases": {"items": []},
        "poisons": {"items": []},
        "features": {"features": []},
        "rules": {"items": []},
    }

    validator = ReferenceValidator(datasets)
    validator.validate_damage_type_refs()
    assert len(validator.errors) == 0


def test_missing_feature_ref():
    """Missing feature references are detected."""
    datasets = {
        "damage_types": {"items": []},
        "monsters": {"items": []},
        "spells": {"items": []},
        "equipment": {"items": []},
        "magic_items": {"items": []},
        "tables": {"items": []},
        "lineages": {"items": []},
        "classes": {
            "items": [
                {
                    "id": "class:barbarian",
                    "features": ["feature:rage", "feature:unarmored_defense"],
                }
            ]
        },
        "ability_scores": {"items": []},
        "skills": {"items": []},
        "weapon_properties": {"items": []},
        "conditions": {"items": []},
        "diseases": {"items": []},
        "poisons": {"items": []},
        "features": {"features": [{"id": "feature:rage"}]},  # missing unarmored_defense
        "rules": {"items": []},
    }

    validator = ReferenceValidator(datasets)
    validator.validate_feature_refs()
    assert len(validator.errors) == 1
    assert "unarmored_defense" in validator.errors[0]


def test_validate_all_returns_false_on_errors():
    """validate_all() returns False when errors exist."""
    datasets = {
        "damage_types": {"items": []},
        "monsters": {"items": []},
        "spells": {"items": []},
        "equipment": {"items": []},
        "magic_items": {"items": []},
        "tables": {"items": []},
        "lineages": {"items": []},
        "classes": {
            "items": [
                {
                    "id": "class:wizard",
                    "features": ["feature:nonexistent"],
                }
            ]
        },
        "ability_scores": {"items": []},
        "skills": {"items": []},
        "weapon_properties": {"items": []},
        "conditions": {"items": []},
        "diseases": {"items": []},
        "poisons": {"items": []},
        "features": {"features": []},
        "rules": {"items": []},
    }

    validator = ReferenceValidator(datasets)
    result = validator.validate_all()
    assert result is False
    assert len(validator.errors) > 0


def test_validate_all_returns_true_on_success():
    """validate_all() returns True when no errors."""
    datasets = {
        "damage_types": {"items": [{"id": "damage:fire"}]},
        "monsters": {"items": []},
        "spells": {"items": []},
        "equipment": {"items": []},
        "magic_items": {"items": []},
        "tables": {"items": []},
        "lineages": {"items": []},
        "classes": {"items": []},
        "ability_scores": {"items": []},
        "skills": {"items": []},
        "weapon_properties": {"items": []},
        "conditions": {"items": []},
        "diseases": {"items": []},
        "poisons": {"items": []},
        "features": {"features": []},
        "rules": {"items": []},
    }

    validator = ReferenceValidator(datasets)
    result = validator.validate_all()
    assert result is True
    assert len(validator.errors) == 0
