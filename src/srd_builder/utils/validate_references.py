"""Cross-reference validation for build-time integrity checks."""

from typing import Any


class ReferenceValidator:
    """Validates cross-dataset references during build."""

    def __init__(self, datasets: dict[str, Any]):
        """Initialize with all datasets."""
        self.datasets = datasets
        self.errors: list[str] = []
        self.warnings: list[str] = []

        # Build ID indexes for fast lookup
        self._build_id_indexes()

    def _build_id_indexes(self) -> None:
        """Build fast lookup indexes for all entity IDs."""
        self.damage_type_ids = {
            dt["id"] for dt in self.datasets.get("damage_types", {}).get("items", []) if "id" in dt
        }
        self.ability_ids = {
            ab["id"]
            for ab in self.datasets.get("ability_scores", {}).get("items", [])
            if "id" in ab
        }
        self.skill_ids = {
            sk["id"] for sk in self.datasets.get("skills", {}).get("items", []) if "id" in sk
        }
        self.condition_ids = {
            cond["id"]
            for cond in self.datasets.get("conditions", {}).get("items", [])
            if "id" in cond
        }
        self.spell_ids = {
            sp["id"] for sp in self.datasets.get("spells", {}).get("items", []) if "id" in sp
        }
        self.feature_ids = {
            feat["id"]
            for feat in self.datasets.get("features", {}).get("features", [])
            if "id" in feat
        }
        self.equipment_ids = {
            item["id"]
            for item in self.datasets.get("equipment", {}).get("items", [])
            if "id" in item
        }
        self.weapon_property_ids = {
            prop["id"]
            for prop in self.datasets.get("weapon_properties", {}).get("items", [])
            if "id" in prop
        }

    def validate_all(self) -> bool:
        """Run all validation checks. Returns True if valid."""
        print("  Checking damage type references...")
        self.validate_damage_type_refs()
        print("  Checking ability references...")
        self.validate_ability_refs()
        print("  Checking skill references...")
        self.validate_skill_refs()
        print("  Checking condition references...")
        self.validate_condition_refs()
        print("  Checking spell references...")
        self.validate_spell_refs()
        print("  Checking feature references...")
        self.validate_feature_refs()
        print("  Checking equipment references...")
        self.validate_equipment_refs()

        if self.errors:
            print(f"\n❌ Found {len(self.errors)} reference errors:")
            for error in self.errors[:20]:  # Limit output
                print(f"  - {error}")
            if len(self.errors) > 20:
                print(f"  ... and {len(self.errors) - 20} more errors")
            return False

        if self.warnings:
            print(f"\n⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings[:10]:
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more warnings")

        return True

    def validate_damage_type_refs(self) -> None:
        """Validate all damage type_id references."""
        # Check monsters
        for monster in self.datasets.get("monsters", {}).get("items", []):
            # Damage arrays in actions
            for action in monster.get("actions", []):
                if effects := action.get("effects", {}):
                    if damage := effects.get("damage"):
                        self._check_ref(
                            damage.get("type_id"),
                            self.damage_type_ids,
                            f"Monster {monster['id']} action {action.get('name', 'unknown')} damage type",
                        )

            # Resistances, immunities, vulnerabilities
            for resist in monster.get("damage_resistances", []):
                if isinstance(resist, dict):
                    self._check_ref(
                        resist.get("type_id"),
                        self.damage_type_ids,
                        f"Monster {monster['id']} resistance",
                    )

            for immunity in monster.get("damage_immunities", []):
                if isinstance(immunity, dict):
                    self._check_ref(
                        immunity.get("type_id"),
                        self.damage_type_ids,
                        f"Monster {monster['id']} immunity",
                    )

            for vuln in monster.get("damage_vulnerabilities", []):
                if isinstance(vuln, dict):
                    self._check_ref(
                        vuln.get("type_id"),
                        self.damage_type_ids,
                        f"Monster {monster['id']} vulnerability",
                    )

        # Check spells
        for spell in self.datasets.get("spells", {}).get("items", []):
            if effects := spell.get("effects", {}):
                if damage := effects.get("damage"):
                    self._check_ref(
                        damage.get("type_id"),
                        self.damage_type_ids,
                        f"Spell {spell['id']} damage type",
                    )

    def validate_ability_refs(self) -> None:
        """Validate all ability_id references."""
        # Check monsters
        for monster in self.datasets.get("monsters", {}).get("items", []):
            # Check action DC ability IDs
            for action in monster.get("actions", []):
                if dc := action.get("dc"):
                    if "dc_type_id" in dc:
                        self._check_ref(
                            dc.get("dc_type_id"),
                            self.ability_ids,
                            f"Monster {monster['id']} action {action.get('name', 'unknown')} DC ability",
                        )

        # Check spells
        for spell in self.datasets.get("spells", {}).get("items", []):
            if effects := spell.get("effects", {}):
                if save := effects.get("save"):
                    # Check if ability_id exists (may not be in all data yet)
                    if "ability_id" in save:
                        self._check_ref(
                            save.get("ability_id"),
                            self.ability_ids,
                            f"Spell {spell['id']} saving throw",
                        )

    def validate_skill_refs(self) -> None:
        """Validate all skill_id references."""
        # Check monsters (if they have skill_id fields)
        for _monster in self.datasets.get("monsters", {}).get("items", []):
            # Current format is {skill_name: bonus}, no skill_id yet
            # This will be relevant when we add skill_id to skills
            pass

    def validate_condition_refs(self) -> None:
        """Validate all condition_id references."""
        # Check monsters
        for monster in self.datasets.get("monsters", {}).get("items", []):
            for cond in monster.get("condition_immunities", []):
                if isinstance(cond, dict):
                    self._check_ref(
                        cond.get("id"),
                        self.condition_ids,
                        f"Monster {monster['id']} condition immunity",
                    )
                elif isinstance(cond, str):
                    # String format: convert to expected ID format
                    expected_id = f"condition:{cond.lower().replace(' ', '_')}"
                    if expected_id not in self.condition_ids:
                        self.warnings.append(
                            f"Monster {monster['id']} condition immunity: {cond} (string format, expected: {expected_id})"
                        )

        # Check spells (if they inflict conditions)
        for spell in self.datasets.get("spells", {}).get("items", []):
            for cond in spell.get("inflicts_conditions", []):
                if isinstance(cond, dict):
                    self._check_ref(
                        cond.get("condition_id"),
                        self.condition_ids,
                        f"Spell {spell['id']} inflicted condition",
                    )

    def validate_spell_refs(self) -> None:
        """Validate spell cross-references (innate casting, magic items)."""
        # Check monster innate spellcasting
        for monster in self.datasets.get("monsters", {}).get("items", []):
            spellcasting = monster.get("innate_spellcasting", {})
            for spell_ref in spellcasting.get("spells", []):
                if isinstance(spell_ref, dict):
                    self._check_ref(
                        spell_ref.get("spell_id"),
                        self.spell_ids,
                        f"Monster {monster['id']} innate spell",
                    )

        # Check magic items that grant spells
        for item in self.datasets.get("magic_items", {}).get("items", []):
            for spell_ref in item.get("grants_spells", []):
                if isinstance(spell_ref, dict):
                    self._check_ref(
                        spell_ref.get("spell_id"),
                        self.spell_ids,
                        f"Magic item {item['id']} granted spell",
                    )

    def validate_feature_refs(self) -> None:
        """Validate feature cross-references (classes, lineages)."""
        # Check classes
        for cls in self.datasets.get("classes", {}).get("items", []):
            for feature_id in cls.get("features", []):
                if isinstance(feature_id, str):
                    self._check_ref(
                        feature_id,
                        self.feature_ids,
                        f"Class {cls['id']} feature",
                    )

        # Check lineages
        for lineage in self.datasets.get("lineages", {}).get("items", []):
            for feature_id in lineage.get("features", []):
                if isinstance(feature_id, str):
                    self._check_ref(
                        feature_id,
                        self.feature_ids,
                        f"Lineage {lineage['id']} feature",
                    )

    def validate_equipment_refs(self) -> None:
        """Validate equipment cross-references (packs, magic items)."""
        # Check equipment packs
        for item in self.datasets.get("equipment", {}).get("items", []):
            for pack_item in item.get("pack_contents", []):
                if isinstance(pack_item, dict):
                    self._check_ref(
                        pack_item.get("item_id"),
                        self.equipment_ids,
                        f"Equipment {item['id']} pack contents",
                    )

        # Check magic items base_item_id
        for item in self.datasets.get("magic_items", {}).get("items", []):
            if base_id := item.get("base_item_id"):
                self._check_ref(
                    base_id,
                    self.equipment_ids,
                    f"Magic item {item['id']} base item",
                )

    def _check_ref(self, ref_id: str | None, valid_ids: set[str], context: str) -> None:
        """Check single reference, record error if invalid."""
        if not ref_id:
            return  # Optional reference

        # Try exact match first
        if ref_id in valid_ids:
            return

        # Try with damage: prefix (backward compatibility)
        if f"damage:{ref_id}" in valid_ids:
            return

        # Try with ability: prefix
        if f"ability:{ref_id}" in valid_ids:
            return

        # Try with skill: prefix
        if f"skill:{ref_id}" in valid_ids:
            return

        # Try with condition: prefix
        if f"condition:{ref_id}" in valid_ids:
            return

        # No match found
        self.errors.append(f"{context}: {ref_id} not found")


def validate_references(datasets: dict[str, Any]) -> bool:
    """Validate all cross-references in datasets. Returns True if valid."""
    validator = ReferenceValidator(datasets)
    return validator.validate_all()
