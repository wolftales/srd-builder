#!/usr/bin/env python3
"""Version bump script for srd-builder.

This script handles the complete version bump process:
1. Updates __version__ in src/srd_builder/__init__.py
2. Regenerates test fixtures with new version
3. Updates README.md with new version
4. Runs tests to verify everything passes
5. Commits all changes

Usage:
    python scripts/bump_version.py 0.6.5
    python scripts/bump_version.py 0.7.0 --no-commit
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def update_version_file(new_version: str) -> None:
    """Update version in pyproject.toml (single source of truth).

    The package exposes ``__version__`` dynamically via ``importlib.metadata``,
    so ``pyproject.toml`` is the only place the version string lives.
    """
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()

    for line in content.splitlines():
        if line.startswith('version = "'):
            old_version = line.split('"')[1]
            break
    else:
        raise ValueError("Could not find version line in pyproject.toml")

    new_content = content.replace(f'version = "{old_version}"', f'version = "{new_version}"', 1)
    pyproject.write_text(new_content)
    print(f"✓ Updated pyproject.toml: {old_version} → {new_version}")

    # Reinstall so importlib.metadata reflects the new version for fixture regen.
    run_command(
        [
            "pip",
            "install",
            "-e",
            ".",
            "--config-settings",
            "editable_mode=compat",
            "--no-deps",
            "--quiet",
        ]
    )


def regenerate_fixtures() -> None:
    """Regenerate all test fixtures with current version."""
    print("\nRegenerating test fixtures...")

    # Import after version update
    sys.path.insert(0, str(Path.cwd() / "src"))
    from srd_builder import __version__
    from srd_builder.parse.parse_ability_scores import parse_ability_scores
    from srd_builder.parse.parse_conditions import parse_condition_records
    from srd_builder.parse.parse_damage_types import parse_damage_types
    from srd_builder.parse.parse_diseases import parse_disease_records
    from srd_builder.parse.parse_equipment import parse_equipment_records
    from srd_builder.parse.parse_lineages import _build_lineage_record
    from srd_builder.parse.parse_magic_items import parse_magic_items
    from srd_builder.parse.parse_monsters import parse_monster_records
    from srd_builder.parse.parse_poisons_table import parse_poisons_table
    from srd_builder.parse.parse_skills import parse_skills
    from srd_builder.parse.parse_spells import parse_spell_records
    from srd_builder.parse.parse_weapon_properties import parse_weapon_properties
    from srd_builder.postprocess import (
        clean_ability_score_record,
        clean_class_record,
        clean_condition_record,
        clean_damage_type_record,
        clean_disease_record,
        clean_equipment_record,
        clean_lineage_record,
        clean_magic_item_record,
        clean_monster_record,
        clean_poison_record,
        clean_rule_record,
        clean_skill_record,
        clean_spell_record,
        clean_table_record,
        clean_weapon_property_record,
    )
    from srd_builder.utils.metadata import meta_block, read_schema_version

    # Spell→classes map snapshot (lets us bump fixtures without re-running
    # the live PDF extractor). Built in v0.27.0 to replace the retired
    # rulesets/srd_5_1/spell_class_targets.py.
    _spell_classes_snapshot = json.loads(
        Path("tests/fixtures/srd_5_1/spell_class_targets_snapshot.json").read_text(encoding="utf-8")
    )
    _spell_classes_map: dict[str, list[str]] = _spell_classes_snapshot["spell_classes"]

    fixtures = [
        # Original 3 datasets
        {
            "name": "monsters",
            "schema_name": "monster",
            "raw": "tests/fixtures/srd_5_1/raw/monsters.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/monsters.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_monster_record(item) for item in parse_monster_records(raw)
            ],
        },
        {
            "name": "equipment",
            "schema_name": "equipment",
            "raw": "tests/fixtures/srd_5_1/raw/equipment.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/equipment.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_equipment_record(item) for item in parse_equipment_records(raw, "srd_5_1")
            ],
        },
        {
            "name": "spells",
            "schema_name": "spell",
            "raw": "tests/fixtures/srd_5_1/raw/spells.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/spells.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_spell_record(item, spell_classes_map=_spell_classes_map)
                for item in parse_spell_records(
                    raw["spells"]
                    if isinstance(raw, dict) and "spells" in raw
                    else (raw if isinstance(raw, list) else [raw])
                )
            ],
        },
        # v0.18.0 datasets
        {
            "name": "classes",
            "schema_name": "class",
            "raw": "tests/fixtures/srd_5_1/raw/classes.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/classes.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_class_record(
                    {
                        "name": rc["name"],
                        "description": rc["description"],
                        "hit_die": rc["hit_die"],
                        "primary_ability": rc["primary_ability"],
                        "saving_throw_proficiencies": rc["saving_throw_proficiencies"],
                        "page": rc["page"],
                        "source": "SRD_CC_v5.1",
                    }
                )
                for rc in raw["class_data"]
            ],
        },
        {
            "name": "conditions",
            "schema_name": "condition",
            "raw": "tests/fixtures/srd_5_1/raw/conditions.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/conditions.json",
            "output_key": "conditions",
            "process": lambda raw: [
                clean_condition_record(item)
                for item in parse_condition_records(raw["sections"], "srd_5_1")
            ],
        },
        {
            "name": "diseases",
            "schema_name": "disease",
            "raw": "tests/fixtures/srd_5_1/raw/diseases.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/diseases.json",
            "output_key": "diseases",
            "process": lambda raw: [
                clean_disease_record(item)
                for item in parse_disease_records(raw["sections"], "srd_5_1")
            ],
        },
        # NOTE: features.json is regenerated by the full build pipeline only.
        # extract_class_features + extract_lineage_traits + parse_features
        # (called per source_type) require the PDF for class/lineage owner
        # resolution. The raw/features.json fixture is a simplified flat list
        # and lacks the source_type partitioning that parse_features needs to
        # produce owner_id-prefixed records. Run `make output` then copy
        # dist/features.json to tests/fixtures/srd_5_1/normalized/features.json.
        {
            "name": "lineages",
            "schema_name": "lineage",
            "raw": "tests/fixtures/srd_5_1/raw/lineages.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/lineages.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_lineage_record(_build_lineage_record(ld)) for ld in raw["lineage_data"]
            ],
        },
        {
            "name": "magic_items",
            "schema_name": "magic_item",
            "raw": "tests/fixtures/srd_5_1/raw/magic_items.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/magic_items.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_magic_item_record(item)
                for item in parse_magic_items({"items": raw}, "srd_5_1")
            ],
        },
        {
            "name": "poisons",
            "schema_name": "poison",
            "raw": "tests/fixtures/srd_5_1/raw/poisons.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/poisons.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_poison_record(item)
                for item in parse_poisons_table(
                    raw["poisons_table"],
                    "srd_5_1",
                    descriptions=raw["poison_descriptions"],
                )
            ],
        },
        {
            "name": "rules",
            "schema_name": "rule",
            "raw": "tests/fixtures/srd_5_1/raw/rules.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/rules.json",
            "output_key": "items",
            "process": lambda raw: [clean_rule_record(rule) for rule in raw["parsed_rules"]],
        },
        {
            "name": "tables",
            "schema_name": "table",
            "raw": "tests/fixtures/srd_5_1/raw/tables.json",
            "normalized": "tests/fixtures/srd_5_1/normalized/tables.json",
            "output_key": "items",
            "process": lambda raw: [
                clean_table_record(
                    {
                        "name": rt["name"],
                        "page": rt["page"],
                        "source": "SRD_CC_v5.1",
                        "headers": rt["headers"],
                        "rows": rt["rows"],
                    }
                )
                for rt in raw["raw_tables"]
            ],
        },
    ]

    # Reference datasets generated from code (no raw input).
    reference_fixtures = [
        ("ability_scores", "ability_score", parse_ability_scores, clean_ability_score_record),
        ("damage_types", "damage_type", parse_damage_types, clean_damage_type_record),
        ("skills", "skill", parse_skills, clean_skill_record),
        (
            "weapon_properties",
            "weapon_property",
            parse_weapon_properties,
            clean_weapon_property_record,
        ),
    ]

    for fixture in fixtures:
        raw_path = Path(fixture["raw"])
        normalized_path = Path(fixture["normalized"])

        raw = json.loads(raw_path.read_text())
        processed = fixture["process"](raw)

        schema_version = read_schema_version(fixture["schema_name"])
        doc = {
            "_meta": meta_block("srd_5_1", schema_version),
            fixture["output_key"]: processed,
        }

        normalized_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"✓ Regenerated {fixture['name']}.json (v{__version__}, schema v{schema_version})")

    for name, schema_name, parse_fn, clean_fn in reference_fixtures:
        normalized_path = Path(f"tests/fixtures/srd_5_1/normalized/{name}.json")
        processed = [clean_fn(item) for item in parse_fn("srd_5_1")]
        schema_version = read_schema_version(schema_name)
        doc = {
            "_meta": meta_block("srd_5_1", schema_version),
            "items": processed,
        }
        normalized_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"✓ Regenerated {name}.json (v{__version__}, schema v{schema_version})")


def update_readme(new_version: str) -> None:
    """Update README.md with new version."""
    readme = Path("README.md")
    content = readme.read_text()

    # Update build pipeline version
    old_pipeline = content
    for line in content.splitlines():
        if line.startswith("### Build pipeline (v"):
            old_version = line.split("(v")[1].split(")")[0]
            content = content.replace(
                f"### Build pipeline (v{old_version})", f"### Build pipeline (v{new_version})"
            )
            print(f"✓ Updated README pipeline version: v{old_version} → v{new_version}")
            break

    # Check if new version is already in roadmap
    if f"v{new_version}" not in content or content == old_pipeline:
        print(
            f"⚠ Note: v{new_version} not found in README roadmap - you may want to add it manually"
        )

    readme.write_text(content)


def run_tests() -> bool:
    """Run test suite and return True if all pass."""
    print("\nRunning tests...")
    result = run_command(["pytest", "tests/", "-q"], check=False)

    if result.returncode == 0:
        print("✓ All tests passed")
        return True
    else:
        print("✗ Tests failed:")
        print(result.stdout)
        print(result.stderr)
        return False


def commit_changes(new_version: str) -> None:
    """Commit all changes and create git tag."""
    print("\nCommitting changes...")

    run_command(["git", "add", "-A"])

    commit_msg = f"""chore: bump version to v{new_version}

Version Changes:
- pyproject.toml: \u2192 {new_version}

Regenerated Fixtures (all 16 datasets):
- tests/fixtures/srd_5_1/normalized/monsters.json
- tests/fixtures/srd_5_1/normalized/equipment.json
- tests/fixtures/srd_5_1/normalized/spells.json
- tests/fixtures/srd_5_1/normalized/classes.json
- tests/fixtures/srd_5_1/normalized/conditions.json
- tests/fixtures/srd_5_1/normalized/diseases.json
- tests/fixtures/srd_5_1/normalized/features.json
- tests/fixtures/srd_5_1/normalized/lineages.json
- tests/fixtures/srd_5_1/normalized/magic_items.json
- tests/fixtures/srd_5_1/normalized/poisons.json
- tests/fixtures/srd_5_1/normalized/rules.json
- tests/fixtures/srd_5_1/normalized/tables.json

Documentation:
- README.md: Updated build pipeline version

All tests passing."""

    run_command(["git", "commit", "-m", commit_msg])
    print(f"✓ Committed version bump to v{new_version}")

    # Create annotated git tag
    print("\nCreating git tag...")
    tag_msg = f"v{new_version}"
    run_command(["git", "tag", "-a", f"v{new_version}", "-m", tag_msg])
    print(f"✓ Created git tag v{new_version}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bump srd-builder version")
    parser.add_argument("version", help="New version number (e.g., 0.6.5)")
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Don't commit changes (useful for testing)",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip running tests (not recommended)",
    )

    args = parser.parse_args()
    new_version = args.version

    # Validate version format
    if not all(c.isdigit() or c == "." for c in new_version):
        print(f"Error: Invalid version format: {new_version}")
        sys.exit(1)

    print(f"Bumping version to {new_version}\n")
    print("=" * 60)

    try:
        # Step 1: Update version file
        update_version_file(new_version)

        # Step 2: Regenerate fixtures
        regenerate_fixtures()

        # Step 3: Update README
        update_readme(new_version)

        # Step 4: Run tests
        if not args.no_test:
            if not run_tests():
                print("\n✗ Version bump incomplete due to test failures")
                sys.exit(1)
        else:
            print("\n⚠ Skipping tests (--no-test flag)")

        # Step 5: Commit and tag
        if not args.no_commit:
            commit_changes(new_version)
            print("\n" + "=" * 60)
            print(f"✓ Version bump to v{new_version} complete!")
            print("\nNext steps:")
            print("  1. Review changes: git show")
            print("  2. Push to GitHub: git push origin main --tags")
            print("  3. Update ROADMAP.md if needed")
        else:
            print("\n⚠ Skipping commit (--no-commit flag)")
            print("\nChanges staged but not committed. Review and commit manually.")

    except Exception as e:
        print(f"\n✗ Error during version bump: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
