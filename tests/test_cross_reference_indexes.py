"""Tests for cross-reference index building."""

from __future__ import annotations

from srd_builder.assemble.indexer import build_cross_reference_indexes


class TestCrossReferenceIndexes:
    """Test cross-reference index generation."""

    def test_spells_by_damage_type(self) -> None:
        """Spells are indexed by their damage type_id."""
        damage_types = [
            {"id": "damage:fire", "name": "Fire"},
            {"id": "damage:cold", "name": "Cold"},
        ]
        spells = [
            {
                "id": "spell:fireball",
                "name": "Fireball",
                "effects": {"damage": {"type_id": "damage:fire", "dice": "8d6"}},
            },
            {
                "id": "spell:fire_bolt",
                "name": "Fire Bolt",
                "effects": {"damage": {"type_id": "damage:fire", "dice": "1d10"}},
            },
            {
                "id": "spell:ray_of_frost",
                "name": "Ray of Frost",
                "effects": {"damage": {"type_id": "damage:cold", "dice": "1d8"}},
            },
        ]

        xref = build_cross_reference_indexes(
            damage_types=damage_types,
            spells=spells,
        )

        assert "spells_by_damage_type" in xref
        assert xref["spells_by_damage_type"]["damage:fire"] == [
            "spell:fire_bolt",
            "spell:fireball",
        ]
        assert xref["spells_by_damage_type"]["damage:cold"] == ["spell:ray_of_frost"]

    def test_monsters_immune_to_damage_type(self) -> None:
        """Monsters are indexed by damage type immunity."""
        damage_types = [
            {"id": "damage:fire", "name": "Fire"},
            {"id": "damage:poison", "name": "Poison"},
        ]
        monsters = [
            {
                "id": "monster:fire_elemental",
                "name": "Fire Elemental",
                "damage_immunities": [{"type": "fire", "type_id": "damage:fire"}],
            },
            {
                "id": "monster:iron_golem",
                "name": "Iron Golem",
                "damage_immunities": [
                    {"type": "fire", "type_id": "damage:fire"},
                    {"type": "poison", "type_id": "damage:poison"},
                ],
            },
        ]

        xref = build_cross_reference_indexes(
            damage_types=damage_types,
            monsters=monsters,
        )

        assert "monsters_immune_to_damage_type" in xref
        fire_immune = xref["monsters_immune_to_damage_type"]["damage:fire"]
        assert "monster:fire_elemental" in fire_immune
        assert "monster:iron_golem" in fire_immune
        assert xref["monsters_immune_to_damage_type"]["damage:poison"] == ["monster:iron_golem"]

    def test_monsters_resistant_to_damage_type(self) -> None:
        """Monsters are indexed by damage type resistance."""
        damage_types = [{"id": "damage:cold", "name": "Cold"}]
        monsters = [
            {
                "id": "monster:white_dragon",
                "name": "White Dragon",
                "damage_resistances": [{"type": "cold", "type_id": "damage:cold"}],
            },
        ]

        xref = build_cross_reference_indexes(
            damage_types=damage_types,
            monsters=monsters,
        )

        assert "monsters_resistant_to_damage_type" in xref
        assert xref["monsters_resistant_to_damage_type"]["damage:cold"] == ["monster:white_dragon"]

    def test_monsters_vulnerable_to_damage_type(self) -> None:
        """Monsters are indexed by damage type vulnerability."""
        damage_types = [{"id": "damage:fire", "name": "Fire"}]
        monsters = [
            {
                "id": "monster:treant",
                "name": "Treant",
                "damage_vulnerabilities": [{"type": "fire", "type_id": "damage:fire"}],
            },
        ]

        xref = build_cross_reference_indexes(
            damage_types=damage_types,
            monsters=monsters,
        )

        assert "monsters_vulnerable_to_damage_type" in xref
        assert xref["monsters_vulnerable_to_damage_type"]["damage:fire"] == ["monster:treant"]

    def test_monsters_immune_to_condition(self) -> None:
        """Monsters are indexed by condition immunity."""
        conditions = [
            {"id": "condition:charmed", "name": "Charmed"},
            {"id": "condition:frightened", "name": "Frightened"},
        ]
        monsters = [
            {
                "id": "monster:lich",
                "name": "Lich",
                "condition_immunities": [
                    {"name": "charmed", "condition_id": "condition:charmed"},
                    {"name": "frightened", "condition_id": "condition:frightened"},
                ],
            },
        ]

        xref = build_cross_reference_indexes(
            conditions=conditions,
            monsters=monsters,
        )

        assert "monsters_immune_to_condition" in xref
        assert xref["monsters_immune_to_condition"]["condition:charmed"] == ["monster:lich"]
        assert xref["monsters_immune_to_condition"]["condition:frightened"] == ["monster:lich"]

    def test_empty_inputs_produce_empty_indexes(self) -> None:
        """Empty or None inputs produce empty cross-references."""
        xref = build_cross_reference_indexes()
        assert xref == {}

        xref = build_cross_reference_indexes(monsters=[], spells=[], damage_types=[])
        # Should have keys but empty values
        assert xref.get("spells_by_damage_type", {}) == {}

    def test_invalid_type_id_not_indexed(self) -> None:
        """Type IDs not in reference dataset are not indexed."""
        damage_types = [{"id": "damage:fire", "name": "Fire"}]
        monsters = [
            {
                "id": "monster:test",
                "name": "Test",
                "damage_immunities": [
                    {"type": "arcane", "type_id": "damage:arcane"}  # Not valid
                ],
            },
        ]

        xref = build_cross_reference_indexes(
            damage_types=damage_types,
            monsters=monsters,
        )

        # Should not contain the invalid type
        assert "damage:arcane" not in xref.get("monsters_immune_to_damage_type", {})

    def test_cross_references_sorted(self) -> None:
        """Cross-reference lists are sorted for deterministic output."""
        damage_types = [{"id": "damage:fire", "name": "Fire"}]
        spells = [
            {"id": "spell:z_spell", "effects": {"damage": {"type_id": "damage:fire"}}},
            {"id": "spell:a_spell", "effects": {"damage": {"type_id": "damage:fire"}}},
            {"id": "spell:m_spell", "effects": {"damage": {"type_id": "damage:fire"}}},
        ]

        xref = build_cross_reference_indexes(damage_types=damage_types, spells=spells)

        fire_spells = xref["spells_by_damage_type"]["damage:fire"]
        assert fire_spells == ["spell:a_spell", "spell:m_spell", "spell:z_spell"]
