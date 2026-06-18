"""Build scaffold for srd-builder.

The goal of this module is to provide a deterministic entry point that
creates predictable output directories without attempting to parse SRD
content yet. Future implementations will replace the stubbed pieces
with real extraction logic.
"""

from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from . import __version__
from .assemble.assemble_equipment import assemble_equipment_from_tables
from .assemble.assemble_prose import assemble_prose_dataset
from .assemble.indexer import build_indexes
from .constants import DIST_DIRNAME, EXEMPLARS_DIRNAME, RULESETS_DIRNAME, SCHEMAS_DIRNAME
from .extract import extract_tables_to_json
from .extract.datasets.extract_classes import extract_classes
from .extract.datasets.extract_equipment import extract_equipment
from .extract.datasets.extract_equipment_packs import extract_equipment_packs
from .extract.datasets.extract_features import extract_class_features, extract_lineage_traits
from .extract.datasets.extract_lineages import extract_lineages
from .extract.datasets.extract_magic_items import extract_magic_items
from .extract.datasets.extract_monsters import extract_monsters
from .extract.datasets.extract_pdf_metadata import extract_pdf_metadata
from .extract.datasets.extract_rules import extract_rules
from .extract.datasets.extract_spell_classes import (
    build_spell_to_classes_map,
    extract_spell_classes,
)
from .extract.datasets.extract_spells import extract_spells
from .extract.extraction_metadata import TABLES
from .parse.parse_ability_scores import parse_ability_scores
from .parse.parse_classes import parse_classes
from .parse.parse_conditions import parse_condition_records
from .parse.parse_damage_types import parse_damage_types
from .parse.parse_diseases import parse_disease_records
from .parse.parse_equipment import parse_equipment_records
from .parse.parse_features import parse_features
from .parse.parse_lineages import parse_lineages
from .parse.parse_magic_items import parse_magic_items
from .parse.parse_monsters import parse_monster_records
from .parse.parse_poison_descriptions import parse_poison_description_records
from .parse.parse_poisons_table import parse_poisons_table
from .parse.parse_rules import parse_rules
from .parse.parse_skills import parse_skills
from .parse.parse_spells import parse_spell_records
from .parse.parse_tables import parse_single_table
from .parse.parse_weapon_properties import parse_weapon_properties
from .postprocess import (
    clean_ability_score_record,
    clean_class_record,
    clean_damage_type_record,
    clean_equipment_record,
    clean_feature_record,
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
from .utils.metadata import (
    DATASET_TO_SCHEMA,
    generate_meta_json,
    read_schema_version,
    wrap_with_meta,
)
from .utils.table_indexer import TableIndexer
from .utils.validate_references import validate_references


def _load_raw_monsters(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw monster data from extraction output.

    Tries monsters_raw.json first (v0.3.0 extraction format),
    falls back to monsters.json (legacy TabylTop format).
    """
    # Try v0.3.0 extraction format first
    raw_source = raw_dir / "monsters_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "monsters" in data:
            return data["monsters"]
        raise TypeError("monsters_raw.json must contain 'monsters' key with array")

    # Fall back to legacy format
    legacy_source = raw_dir / "monsters.json"
    if legacy_source.exists():
        data = json.loads(legacy_source.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise TypeError("ruleset raw monsters must be stored as a JSON array")
        return data

    return []


def _render_json(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def _write_datasets(  # noqa: PLR0913
    *,
    ruleset: str,
    dist_data_dir: Path,
    monsters: list[dict[str, Any]],
    equipment: list[dict[str, Any]] | None = None,
    spells: list[dict[str, Any]] | None = None,
    magic_items: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    lineages: list[dict[str, Any]] | None = None,
    classes: list[dict[str, Any]] | None = None,
    ability_scores: list[dict[str, Any]] | None = None,
    damage_types: list[dict[str, Any]] | None = None,
    skills: list[dict[str, Any]] | None = None,
    weapon_properties: list[dict[str, Any]] | None = None,
    conditions: dict[str, Any] | None = None,  # Prose dataset document
    diseases: dict[str, Any] | None = None,  # Prose dataset document
    poisons: dict[str, Any] | None = None,  # Prose dataset document
    features: dict[str, Any] | None = None,  # Prose dataset document
    rules: list[dict[str, Any]] | None = None,
    spell_classes_map: dict[str, list[str]] | None = None,
) -> None:
    processed_monsters = [clean_monster_record(monster) for monster in monsters]

    monsters_doc = wrap_with_meta(
        {"items": processed_monsters},
        ruleset=ruleset,
        schema_version=read_schema_version("monster"),
    )
    (dist_data_dir / "monsters.json").write_text(
        _render_json(monsters_doc),
        encoding="utf-8",
    )

    # Write equipment if available
    processed_equipment = None
    if equipment:
        processed_equipment = [clean_equipment_record(item) for item in equipment]
        equipment_doc = wrap_with_meta(
            {"items": processed_equipment},
            ruleset=ruleset,
            schema_version=read_schema_version("equipment"),
        )

        # Add equipment-specific metadata (SRD economic rules)
        equipment_doc["_meta"]["equipment_economics"] = {
            "resale_rules": {
                "arms_armor_equipment": "Undamaged weapons, armor, and other equipment fetch half their cost when sold in a market. Weapons and armor used by monsters are rarely in good enough condition to sell.",
                "magic_items": "Selling magic items is problematic. Finding someone to buy a potion or a scroll isn't too hard, but other items are out of the realm of most but the wealthiest nobles. The value of magic is far beyond simple gold.",
                "gems_jewelry_art": "These items retain their full value in the marketplace, and you can either trade them in for coin or use them as currency for other transactions.",
                "trade_goods": "Like gems and art objects, trade goods—bars of iron, bags of salt, livestock, and so on—retain their full value in the marketplace and barter economy.",
            },
            "default_resale_multiplier": 0.5,
            "source_page": 62,
        }

        (dist_data_dir / "equipment.json").write_text(
            _render_json(equipment_doc),
            encoding="utf-8",
        )

    # Write spells (always write, even if empty, to maintain consistent structure)
    processed_spells = None
    if spells is not None:
        processed_spells = [
            clean_spell_record(spell, spell_classes_map=spell_classes_map) for spell in spells
        ]
    else:
        processed_spells = []

    spells_doc = wrap_with_meta(
        {"items": processed_spells},
        ruleset=ruleset,
        schema_version=read_schema_version("spell"),
    )
    (dist_data_dir / "spells.json").write_text(
        _render_json(spells_doc),
        encoding="utf-8",
    )

    # Write magic items (v0.16.0)
    # Parse extracts structure, postprocess normalizes (following modular pattern)
    processed_magic_items = (
        [clean_magic_item_record(item) for item in magic_items] if magic_items else []
    )

    magic_items_doc = wrap_with_meta(
        {"items": processed_magic_items},
        ruleset=ruleset,
        schema_version=read_schema_version("magic_item"),
    )
    (dist_data_dir / "magic_items.json").write_text(
        _render_json(magic_items_doc),
        encoding="utf-8",
    )

    # Write tables (v0.7.0)
    # Postprocess: normalize IDs and polish text
    processed_tables = [clean_table_record(t) for t in tables] if tables else None
    if processed_tables:
        # Sort tables by page number (document/TOC order)
        def get_sort_page(table: dict[str, Any]) -> int:
            page = table.get("page")
            if page is None:
                return 99999  # Put tables without pages at end
            if isinstance(page, list):
                return page[0] if page else 99999
            return page

        sorted_tables = sorted(processed_tables, key=lambda t: (get_sort_page(t), t.get("id", "")))

        # Reorder table properties: metadata first, columns and rows at end
        reordered_tables = []
        for table in sorted_tables:
            ordered = {}
            # Core identification first
            for key in ["id", "simple_name", "name"]:
                if key in table:
                    ordered[key] = table[key]
            # Metadata fields
            for key in ["page", "category", "section", "notes", "summary"]:
                if key in table:
                    ordered[key] = table[key]
            # Any other fields (except columns/rows)
            for key, value in table.items():
                if key not in ordered and key not in ["columns", "rows"]:
                    ordered[key] = value
            # Columns and rows at the very end
            if "columns" in table:
                ordered["columns"] = table["columns"]
            if "rows" in table:
                ordered["rows"] = table["rows"]
            reordered_tables.append(ordered)

        tables_doc = wrap_with_meta(
            {"items": reordered_tables},
            ruleset=ruleset,
            schema_version=read_schema_version("table"),
        )
        (dist_data_dir / "tables.json").write_text(
            _render_json(tables_doc),
            encoding="utf-8",
        )

    # Write lineages (v0.8.0)
    # Postprocess: normalize IDs and polish text
    processed_lineages = [clean_lineage_record(lin) for lin in lineages] if lineages else None
    if processed_lineages:
        lineages_doc = wrap_with_meta(
            {"items": processed_lineages},
            ruleset=ruleset,
            schema_version=read_schema_version("lineage"),
        )
        (dist_data_dir / "lineages.json").write_text(
            _render_json(lineages_doc),
            encoding="utf-8",
        )

    # Write classes (v0.8.2)
    # Postprocess: normalize IDs and polish text
    processed_classes = [clean_class_record(c) for c in classes] if classes else None
    if processed_classes:
        classes_doc = wrap_with_meta(
            {"items": processed_classes},
            ruleset=ruleset,
            schema_version=read_schema_version("class"),
        )
        (dist_data_dir / "classes.json").write_text(
            _render_json(classes_doc),
            encoding="utf-8",
        )

    # Write ability_scores (v0.20.0)
    # Atomic reference dataset: 6 core D&D ability scores
    # Static data from SRD pages 76-78, no PDF extraction required
    processed_ability_scores = (
        [clean_ability_score_record(a) for a in ability_scores] if ability_scores else None
    )
    if processed_ability_scores:
        ability_scores_doc = wrap_with_meta(
            {"items": processed_ability_scores},
            ruleset=ruleset,
            schema_version=read_schema_version("ability_score"),
        )
        (dist_data_dir / "ability_scores.json").write_text(
            _render_json(ability_scores_doc),
            encoding="utf-8",
        )

    # Write damage_types (v0.20.0)
    # Atomic reference dataset: 13 canonical D&D damage types
    # Static data from SRD page 97, no PDF extraction required
    processed_damage_types = (
        [clean_damage_type_record(dt) for dt in damage_types] if damage_types else None
    )
    if processed_damage_types:
        damage_types_doc = wrap_with_meta(
            {"items": processed_damage_types},
            ruleset=ruleset,
            schema_version=read_schema_version("damage_type"),
        )
        (dist_data_dir / "damage_types.json").write_text(
            _render_json(damage_types_doc),
            encoding="utf-8",
        )

    # Write skills (v0.20.0)
    # Atomic reference dataset: 18 D&D 5e skills
    # Static data from SRD pages 76-79, no PDF extraction required
    processed_skills = [clean_skill_record(s) for s in skills] if skills else None
    if processed_skills:
        skills_doc = wrap_with_meta(
            {"items": processed_skills},
            ruleset=ruleset,
            schema_version=read_schema_version("skill"),
        )
        (dist_data_dir / "skills.json").write_text(
            _render_json(skills_doc),
            encoding="utf-8",
        )

    # Write weapon_properties (v0.20.0)
    # Atomic reference dataset: 11 D&D 5e weapon properties
    # Static data from SRD page 147, no PDF extraction required
    processed_weapon_properties = (
        [clean_weapon_property_record(wp) for wp in weapon_properties]
        if weapon_properties
        else None
    )
    if processed_weapon_properties:
        weapon_properties_doc = wrap_with_meta(
            {"items": processed_weapon_properties},
            ruleset=ruleset,
            schema_version=read_schema_version("weapon_property"),
        )
        (dist_data_dir / "weapon_properties.json").write_text(
            _render_json(weapon_properties_doc),
            encoding="utf-8",
        )

    # Write conditions (v0.10.0)
    # Conditions are already fully normalized by build_conditions, no additional cleaning needed
    processed_conditions = None
    if conditions:
        # Conditions come as a complete document with _meta already included
        (dist_data_dir / "conditions.json").write_text(
            _render_json(conditions),
            encoding="utf-8",
        )
        # Extract just the conditions list for indexing
        processed_conditions = conditions.get("conditions", [])

    # Write diseases (v0.11.0)
    processed_diseases = None
    if diseases:
        (dist_data_dir / "diseases.json").write_text(
            _render_json(diseases),
            encoding="utf-8",
        )
        processed_diseases = diseases.get("diseases", [])

    # Write poisons (v0.11.0)
    # Poisons is a single table record (like madness tables)
    processed_poisons = None
    if poisons:
        (dist_data_dir / "poisons.json").write_text(
            _render_json(poisons),
            encoding="utf-8",
        )
        # Extract just the items list for indexing
        processed_poisons = poisons.get("items", [])

    # Write features (v0.11.0)
    processed_features = None
    if features:
        (dist_data_dir / "features.json").write_text(
            _render_json(features),
            encoding="utf-8",
        )
        # Extract just the features list for indexing
        processed_features = features.get("features", [])

    # Write rules (v0.17.0)
    # Parse extracts structure, postprocess normalizes (following modular pattern)
    processed_rules = None
    if rules:
        processed_rules = [clean_rule_record(rule) for rule in rules]
        rules_doc = wrap_with_meta(
            {"items": processed_rules},
            ruleset=ruleset,
            schema_version=read_schema_version("rule"),
        )
        (dist_data_dir / "rules.json").write_text(
            _render_json(rules_doc),
            encoding="utf-8",
        )

    index_payload = build_indexes(
        processed_monsters,
        processed_spells,
        processed_equipment,
        processed_magic_items,
        processed_tables,
        processed_lineages,
        processed_classes,
        processed_conditions,
        processed_diseases,
        processed_poisons,
        processed_features,
        processed_rules,
        processed_damage_types,
        processed_ability_scores,
        processed_skills,
    )

    # Build cross-reference indexes (v0.21.0 - Phase 2)
    # These enable reverse lookups: "which spells deal fire damage?"
    from srd_builder.assemble.indexer import build_cross_reference_indexes

    cross_references = build_cross_reference_indexes(
        monsters=processed_monsters,
        spells=processed_spells,
        equipment=processed_equipment,
        magic_items=processed_magic_items,
        damage_types=processed_damage_types,
        conditions=processed_conditions,
        skills=processed_skills,
    )

    if cross_references:
        index_payload["cross_references"] = cross_references

    # Index doesn't have a formal schema yet - use generic version
    index_doc = wrap_with_meta(
        index_payload,
        ruleset=ruleset,
        schema_version="1.0.0",
    )
    (dist_data_dir / "index.json").write_text(
        _render_json(index_doc),
        encoding="utf-8",
    )

    # Validate cross-references AFTER writing all datasets (v0.21.0)
    # Read back the written JSON files to validate actual output
    print("\n🔍 Validating cross-references...")

    def _load_json(filename: str) -> dict[str, Any]:
        path = dist_data_dir / filename
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {"items": []}

    datasets_for_validation = {
        "monsters": _load_json("monsters.json"),
        "equipment": _load_json("equipment.json"),
        "spells": _load_json("spells.json"),
        "magic_items": _load_json("magic_items.json"),
        "tables": _load_json("tables.json"),
        "lineages": _load_json("lineages.json"),
        "classes": _load_json("classes.json"),
        "ability_scores": _load_json("ability_scores.json"),
        "damage_types": _load_json("damage_types.json"),
        "skills": _load_json("skills.json"),
        "weapon_properties": _load_json("weapon_properties.json"),
        "conditions": _load_json("conditions.json"),
        "diseases": _load_json("diseases.json"),
        "poisons": _load_json("poisons.json"),
        "features": _load_json("features.json"),
        "rules": _load_json("rules.json"),
    }

    if validate_references(datasets_for_validation):
        print("✅ All cross-references valid\n")
    else:
        print("\n⚠️  Cross-reference validation found issues.")
        print("    (Validation is informational only in v0.21.0)\n")


@dataclass
class BuildReport:
    """Small metadata payload written alongside build artifacts."""

    ruleset: str
    output_format: str
    timestamp_utc: str
    builder_version: str
    python_version: str

    @classmethod
    def create(cls, ruleset: str, output_format: str) -> BuildReport:
        # The timestamp only lives in the report to aid debugging. Downstream
        # dataset files should remain timestamp-free to keep builds reproducible.
        timestamp = datetime.now(UTC).isoformat()
        return cls(
            ruleset=ruleset,
            output_format=output_format,
            timestamp_utc=timestamp,
            builder_version=__version__,
            python_version=platform.python_version(),
        )

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SRD datasets")
    parser.add_argument(
        "--ruleset",
        required=True,
        help="Ruleset identifier (e.g. srd_5_1)",
    )
    parser.add_argument(
        "--format",
        default="json",
        choices=["json"],
        help="Output format to generate (json only for now)",
    )
    parser.add_argument(
        "--out",
        default=DIST_DIRNAME,
        help="Root output directory for build artifacts",
    )
    parser.add_argument(
        "--bundle",
        action="store_true",
        help="Create complete bundle with schemas and documentation (for production)",
    )
    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="Extract only tables (skip monsters, equipment, spells) for faster iteration",
    )
    parser.add_argument(
        "--monsters-only",
        action="store_true",
        help="Extract only monsters (skip equipment, spells, tables)",
    )
    parser.add_argument(
        "--equipment-only",
        action="store_true",
        help="Extract only equipment (skip monsters, spells, tables)",
    )
    parser.add_argument(
        "--spells-only",
        action="store_true",
        help="Extract only spells (skip monsters, equipment, tables)",
    )
    parser.add_argument(
        "--skip",
        type=str,
        help="Comma-separated list of datasets to skip (e.g. 'monsters,equipment,spells')",
    )
    return parser.parse_args(argv)


def ensure_ruleset_layout(ruleset: str, out_dir: Path) -> dict[str, Path]:
    """Create the directory layout expected for a ruleset build.

    Returns a mapping of key directory names to their resolved paths.
    """

    dist_ruleset_dir = out_dir / ruleset
    ruleset_dir = Path(RULESETS_DIRNAME) / ruleset
    raw_dir = ruleset_dir / "raw"

    dist_ruleset_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    return {
        "dist_ruleset": dist_ruleset_dir,
        "ruleset": ruleset_dir,
        "raw": raw_dir,
    }


def _generate_bundle_readme(target_dir: Path) -> str:
    """Build the bundle README dynamically from the freshly written meta.json.

    The README is regenerated on every build so version, date, schema versions,
    and dataset counts always match the shipped payload.
    """
    meta = json.loads((target_dir / "meta.json").read_text(encoding="utf-8"))
    datasets = meta.get("datasets", {})
    schemas = meta.get("schemas", {})
    builder_version = meta.get("builder_version", __version__)
    ruleset_version = meta.get("ruleset_version", "5.1")
    extracted_at = meta.get("build", {}).get("extracted_at")
    generated_line = extracted_at[:10] if extracted_at else "(reproducible build)"

    total_items = sum(entry.get("count", 0) for entry in datasets.values())

    # Pretty dataset rows: "datasets" key with display name + schema lookup.
    dataset_display = {
        "ability_scores": ("Ability Scores", "ability_score"),
        "classes": ("Classes", "class"),
        "conditions": ("Conditions", "condition"),
        "damage_types": ("Damage Types", "damage_type"),
        "diseases": ("Diseases", "disease"),
        "equipment": ("Equipment", "equipment"),
        "features": ("Features", "features"),
        "lineages": ("Lineages", "lineage"),
        "magic_items": ("Magic Items", "magic_item"),
        "monsters": ("Monsters", "monster"),
        "poisons": ("Poisons", "poison"),
        "rules": ("Rules", "rule"),
        "skills": ("Skills", "skill"),
        "spells": ("Spells", "spell"),
        "tables": ("Tables", "table"),
        "weapon_properties": ("Weapon Properties", "weapon_property"),
    }

    rows = []
    for name in sorted(datasets):
        label, schema_key = dataset_display.get(name, (name.title(), name))
        count = datasets[name].get("count", 0)
        schema_ver = schemas.get(schema_key, "—")
        rows.append(f"| {label} | {count} | `{name}.json` | v{schema_ver} |")
    inventory_table = "\n".join(rows)

    schema_list = "\n".join(
        f"- `{name}.schema.json` — v{schemas[name]}" for name in sorted(schemas)
    )

    return f"""# SRD 5.1 Dataset Bundle

**Builder version:** srd-builder v{builder_version}
**Ruleset:** SRD {ruleset_version} (System Reference Document)
**Generated:** {generated_line}
**Total items:** {total_items} across {len(datasets)} datasets

---

## What's Included

Machine-readable D&D 5e SRD data extracted from the official PDF. Each dataset
ships as a single `*.json` file with a `_meta` block + `items` array.

| Dataset | Items | File | Schema |
|---|---:|---|---|
{inventory_table}

Plus:

- `meta.json` — bundle metadata (versions, license, page index, inventory)
- `build_report.json` — build provenance (timestamps, builder version)
- `index.json` — pre-built search index with alias support
- `schemas/` — JSON Schema files for all datasets
- `docs/` — `SCHEMAS.md`, `DATA_DICTIONARY.md`

---

## Quick Start

```javascript
// Node.js
const monsters = require('./monsters.json');
const dragon = monsters.items.find(m => m.simple_name === 'adult_red_dragon');
console.log(dragon.challenge_rating);  // 17

const spells = require('./spells.json');
const fireball = spells.items.find(s => s.simple_name === 'fireball');
console.log(fireball.level);  // 3
```

```python
# Python
import json

with open('monsters.json') as f:
    monsters = json.load(f)['items']
dragon = next(m for m in monsters if m['id'] == 'monster:adult_red_dragon')

with open('spells.json') as f:
    spells = json.load(f)['items']
fireball = next(s for s in spells if s['simple_name'] == 'fireball')
```

---

## Schemas

All datasets are validated against JSON Schema files in `schemas/`:

{schema_list}

---

## License

This work includes material taken from the System Reference Document 5.1
("SRD 5.1") by Wizards of the Coast LLC, licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/legalcode).

See `meta.json` for full attribution.
"""


def _copy_bundle_collateral(target_dir: Path) -> None:
    """Copy schemas and documentation to create complete bundle.

    For production releases, this assembles the full package with:
    - README.md (generated dynamically from meta.json)
    - schemas/ directory (every dataset schema)
    - schemas/exemplars/ directory (one valid instance per schema)
    - docs/ directory (SCHEMAS.md, DATA_DICTIONARY.md)
    """
    repo_root = Path(__file__).resolve().parents[2]

    # Generate README from live meta.json so it always matches the payload.
    readme_dst = target_dir / "README.md"
    readme_dst.write_text(_generate_bundle_readme(target_dir), encoding="utf-8")
    print("  ✓ Generated README.md")

    # Copy every shipped dataset schema. Source of truth: DATASET_TO_SCHEMA.
    schemas_src = repo_root / SCHEMAS_DIRNAME
    schemas_dst = target_dir / SCHEMAS_DIRNAME
    schemas_dst.mkdir(exist_ok=True)
    schema_names = sorted(set(DATASET_TO_SCHEMA.values()))
    for schema_name in schema_names:
        src = schemas_src / f"{schema_name}.schema.json"
        if src.exists():
            (schemas_dst / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            print(f"  ⚠ Schema not found: {src.name}")
    print(f"  ✓ Copied schemas/ ({len(schema_names)} schemas)")

    # Copy generated exemplars (one minimal valid instance per schema).
    exemplars_src = repo_root / SCHEMAS_DIRNAME / EXEMPLARS_DIRNAME
    if exemplars_src.exists():
        exemplars_dst = schemas_dst / EXEMPLARS_DIRNAME
        exemplars_dst.mkdir(exist_ok=True)
        count = 0
        for src in sorted(exemplars_src.glob("*.exemplar.json")):
            (exemplars_dst / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            count += 1
        print(f"  ✓ Copied schemas/exemplars/ ({count} exemplars)")

    # Copy docs
    docs_src = repo_root / "docs"
    docs_dst = target_dir / "docs"
    docs_dst.mkdir(exist_ok=True)
    for doc_file in ["SCHEMAS.md", "DATA_DICTIONARY.md"]:
        src = docs_src / doc_file
        if src.exists():
            (docs_dst / doc_file).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print("  ✓ Copied docs/")


def _extract_raw_monsters(raw_dir: Path, ruleset_dir: Path) -> Path | None:
    """Extract monsters from PDF if present.

    Returns:
        Path to extracted monsters_raw.json, or None if no PDF found
    """
    pdf_files = sorted(ruleset_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF found; extraction will skip.")
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting monsters from {pdf_path.name}...")

    # Run extraction
    extracted_data = extract_monsters(pdf_path)

    # Write to raw directory
    output_path = raw_dir / "monsters_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    monster_count = extracted_data["_meta"]["monster_count"]
    warnings = extracted_data["_meta"]["total_warnings"]
    print(f"✓ Extracted {monster_count} monsters (warnings: {warnings})")
    print(f"✓ Saved to {output_path}")

    # Update pdf_meta.json with PDF hash (input validation file)
    pdf_meta_path = raw_dir / "pdf_meta.json"
    pdf_meta: dict[str, object]
    if pdf_meta_path.exists():
        pdf_meta = json.loads(pdf_meta_path.read_text(encoding="utf-8"))
        if not isinstance(pdf_meta, dict):
            print(
                f"Warning: {pdf_meta_path} contains JSON that is not an object (got {type(pdf_meta).__name__}); resetting to empty dict.",
            )
            pdf_meta = {}
    else:
        pdf_meta = {}

    pdf_meta["pdf_sha256"] = extracted_data["_meta"]["pdf_sha256"]
    pdf_meta_path.write_text(
        json.dumps(pdf_meta, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    return output_path


def _extract_raw_equipment(raw_dir: Path, ruleset_dir: Path) -> Path | None:
    """Extract equipment from PDF if present.

    Returns:
        Path to extracted equipment_raw.json, or None if no PDF found
    """
    pdf_files = sorted(ruleset_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting equipment from {pdf_path.name}...")

    # Run extraction
    try:
        extracted_data = extract_equipment(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive guard for non-PDF fixtures
        print(f"⚠️ Equipment extraction skipped: {exc}")
        return None

    # Write to raw directory
    output_path = raw_dir / "equipment_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    item_count = extracted_data["_meta"]["items_extracted"]
    warnings = extracted_data["_meta"]["warnings"]
    print(f"✓ Extracted {item_count} equipment items (warnings: {len(warnings)})")
    print(f"✓ Saved to {output_path}")

    return output_path


def _load_raw_equipment(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw equipment data from extraction output."""
    raw_source = raw_dir / "equipment_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "equipment" in data:
            return data["equipment"]
        raise TypeError("equipment_raw.json must contain 'equipment' key with array")
    return []


def _extract_raw_spells(raw_dir: Path, ruleset_dir: Path) -> Path | None:
    """Extract spells from PDF if present.

    Returns:
        Path to extracted spells_raw.json, or None if no PDF found
    """
    pdf_files = sorted(ruleset_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting spells from {pdf_path.name}...")

    # Run extraction
    try:
        extracted_data = extract_spells(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"⚠️ Spell extraction skipped: {exc}")
        return None

    # Write to raw directory
    output_path = raw_dir / "spells_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    spell_count = extracted_data["_meta"]["spell_count"]
    warnings = extracted_data["_meta"]["total_warnings"]
    print(f"✓ Extracted {spell_count} spells (warnings: {warnings})")
    print(f"✓ Saved to {output_path}")

    return output_path


def _load_raw_spells(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw spell data from extraction output."""
    raw_source = raw_dir / "spells_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "spells" in data:
            return data["spells"]
        raise TypeError("spells_raw.json must contain 'spells' key with array")
    return []


def _extract_raw_magic_items(raw_dir: Path, ruleset_dir: Path) -> Path | None:
    """Extract magic items from PDF if present.

    Returns:
        Path to extracted magic_items_raw.json, or None if no PDF found
    """
    pdf_files = sorted(ruleset_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting magic items from {pdf_path.name}...")

    # Run extraction
    try:
        extracted_data = extract_magic_items(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"⚠️ Magic items extraction skipped: {exc}")
        return None

    # Write to raw directory
    output_path = raw_dir / "magic_items_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    item_count = extracted_data["_meta"]["item_count"]
    warnings = extracted_data["_meta"]["total_warnings"]
    print(f"✓ Extracted {item_count} magic items (warnings: {warnings})")
    print(f"✓ Saved to {output_path}")

    return output_path


def _load_raw_magic_items(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw magic items data from extraction output."""
    raw_source = raw_dir / "magic_items_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "items" in data:
            return data["items"]
        raise TypeError("magic_items_raw.json must contain 'items' key with array")
    return []


def _extract_raw_rules(raw_dir: Path, ruleset_dir: Path) -> Path | None:
    """Extract rules from PDF if present.

    Returns:
        Path to extracted rules_raw.json, or None if no PDF found
    """
    pdf_files = sorted(ruleset_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting rules from {pdf_path.name}...")

    # Run extraction
    try:
        extracted_data = extract_rules(pdf_path)
    except Exception as exc:  # pragma: no cover - defensive guard
        print(f"⚠️ Rules extraction skipped: {exc}")
        return None

    # Write to raw directory
    output_path = raw_dir / "rules_raw.json"
    output_path.write_text(
        json.dumps(extracted_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    sections = extracted_data.get("sections", [])
    blocks = extracted_data.get("text_blocks", [])
    print(f"✓ Extracted {len(sections)} sections ({len(blocks)} text blocks)")
    print(f"✓ Saved to {output_path}")

    return output_path


def _load_raw_rules(raw_dir: Path) -> dict[str, Any]:
    """Load raw rules data from extraction output."""
    raw_source = raw_dir / "rules_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "text_blocks" in data:
            return data
        raise TypeError("rules_raw.json must contain 'text_blocks' key")
    return {}


def _extract_raw_tables(raw_dir: Path, ruleset_dir: Path) -> Path | None:
    """Extract reference tables from PDF.

    Returns:
        Path to extracted tables_raw.json, or None if no PDF found
    """
    pdf_files = sorted(ruleset_dir.glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    print(f"Extracting tables from {pdf_path.name}...")

    try:
        output_path = raw_dir / "tables_raw.json"
        extract_tables_to_json(pdf_path, output_path, skip_failures=True)
        print(f"✓ Saved to {output_path}")
        return output_path
    except Exception as exc:  # pragma: no cover
        print(f"⚠️ Table extraction skipped: {exc}")
        return None


def _load_raw_tables(raw_dir: Path) -> list[dict[str, Any]]:
    """Load raw table data from extraction output."""
    raw_source = raw_dir / "tables_raw.json"
    if raw_source.exists():
        data = json.loads(raw_source.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "tables" in data:
            return data["tables"]
        raise TypeError("tables_raw.json must contain 'tables' key with array")
    return []


def _generate_table_page_index(
    raw_dir: Path, extracted_table_ids: list[str] | None = None
) -> dict[str, Any] | None:
    """Generate page_index data from table_indexer for meta.json.

    Args:
        raw_dir: Directory containing the PDF
        extracted_table_ids: List of table IDs that were successfully extracted

    Returns:
        Page index dictionary or None if no PDF found
    """
    pdf_files = sorted(Path(raw_dir).glob("*.pdf"))
    if not pdf_files:
        return None

    pdf_path = pdf_files[0]
    try:
        indexer = TableIndexer(pdf_path)
        page_index = indexer.generate_page_index_for_meta(extracted_table_ids)
        return page_index
    except Exception as exc:  # pragma: no cover
        print(f"⚠️ Table page index generation skipped: {exc}")
        return None


def build(  # noqa: C901
    ruleset: str,
    output_format: str,
    out_dir: Path,
    bundle: bool = False,
    skip_datasets: set[str] | None = None,
) -> Path:
    layout = ensure_ruleset_layout(ruleset=ruleset, out_dir=out_dir)
    target_dir = layout["dist_ruleset"]
    skip_datasets = skip_datasets or set()

    report = BuildReport.create(ruleset=ruleset, output_format=output_format)
    report_path = target_dir / "build_report.json"
    report_path.write_text(report.to_json() + "\n", encoding="utf-8")

    # Extract monsters from PDF (v0.3.0)
    if "monsters" not in skip_datasets:
        _extract_raw_monsters(raw_dir=layout["raw"], ruleset_dir=layout["ruleset"])

    # Extract equipment from PDF (v0.5.0)
    if "equipment" not in skip_datasets:
        _extract_raw_equipment(raw_dir=layout["raw"], ruleset_dir=layout["ruleset"])

    # Extract spells from PDF (v0.6.0)
    if "spells" not in skip_datasets:
        _extract_raw_spells(raw_dir=layout["raw"], ruleset_dir=layout["ruleset"])

    # Extract magic items from PDF (v0.16.0)
    if "magic_items" not in skip_datasets:
        _extract_raw_magic_items(raw_dir=layout["raw"], ruleset_dir=layout["ruleset"])

    # Extract rules from PDF (v0.17.0)
    if "rules" not in skip_datasets:
        _extract_raw_rules(raw_dir=layout["raw"], ruleset_dir=layout["ruleset"])

    # Extract tables from PDF (v0.7.0)
    if "tables" not in skip_datasets:
        _extract_raw_tables(raw_dir=layout["raw"], ruleset_dir=layout["ruleset"])

    raw_monsters = _load_raw_monsters(layout["raw"]) if "monsters" not in skip_datasets else []
    parsed_monsters = parse_monster_records(raw_monsters) if raw_monsters else []

    # Parse tables (v0.7.0) - needed before equipment assembly
    raw_tables = _load_raw_tables(layout["raw"])
    parsed_tables = None
    if raw_tables:
        from .extract.table_targets import TARGET_TABLES

        targets_by_id = {t["id"]: t for t in TARGET_TABLES}
        parsed_tables = [parse_single_table(raw, targets_by_id) for raw in raw_tables]

    # Equipment assembly (v0.9.9) - now uses tables.json instead of PyMuPDF
    parsed_equipment = []
    if "equipment" not in skip_datasets:
        if parsed_tables:
            # Equipment packs are extracted from PDF page 70 (v0.27.5 — see
            # src/srd_builder/extract/datasets/extract_equipment_packs.py;
            # retired hand-curated EQUIPMENT_PACKS literal).
            equipment_packs = None
            ruleset_dir = Path("rulesets") / ruleset
            pdf_files = sorted(ruleset_dir.glob("*.pdf"))
            if pdf_files:
                equipment_packs = extract_equipment_packs(pdf_files[0])["packs"]

            # New table-based assembly (v0.9.9 Part 2)
            parsed_equipment = assemble_equipment_from_tables(
                parsed_tables, ruleset, equipment_packs=equipment_packs
            )
        else:
            # Fallback to old PyMuPDF extraction if no tables available
            raw_equipment = _load_raw_equipment(layout["raw"])
            parsed_equipment = (
                parse_equipment_records(raw_equipment, ruleset) if raw_equipment else []
            )

    raw_spells = _load_raw_spells(layout["raw"]) if "spells" not in skip_datasets else []
    parsed_spells = parse_spell_records(raw_spells) if raw_spells else []

    # Parse magic items (v0.16.0)
    raw_magic_items = (
        _load_raw_magic_items(layout["raw"]) if "magic_items" not in skip_datasets else []
    )
    # parse_magic_items expects a dict with 'items' key (like extract output)
    parsed_magic_items = (
        parse_magic_items({"items": raw_magic_items}, ruleset) if raw_magic_items else []
    )

    # Parse rules (v0.17.0)
    raw_rules = _load_raw_rules(layout["raw"]) if "rules" not in skip_datasets else {}
    parsed_rules = parse_rules(raw_rules, ruleset) if raw_rules else []

    # Parse lineages (v0.8.0; live PDF extraction since v0.27.0)
    pdf_files = sorted(layout["ruleset"].glob("*.pdf"))
    lineage_data: list[dict[str, Any]] = []
    parsed_lineages: list[dict[str, Any]] = []
    class_data: list[dict[str, Any]] = []
    spell_classes_map: dict[str, list[str]] = {}
    if pdf_files:
        try:
            lineage_data = extract_lineages(pdf_files[0])["lineages"]
            parsed_lineages = parse_lineages(lineage_data)
        except Exception as exc:
            print(f"⚠️ Lineage extraction skipped: {exc}")
        try:
            class_data = extract_classes(pdf_files[0])["classes"]
        except Exception as exc:
            print(f"⚠️ Class extraction skipped: {exc}")
        try:
            class_spells = extract_spell_classes(pdf_files[0])["class_spells"]
            spell_classes_map = build_spell_to_classes_map(class_spells)
        except Exception as exc:
            print(f"⚠️ Spell-class extraction skipped: {exc}")

    # Parse classes (v0.8.2; live PDF extraction since v0.27.x)
    parsed_classes = parse_classes(class_data, ruleset) if class_data else []

    # Parse ability_scores (v0.20.0)
    # Ability scores are game constants (6 core abilities: STR, DEX, CON, INT, WIS, CHA)
    parsed_ability_scores = parse_ability_scores(ruleset)

    # Parse damage_types (v0.20.0)
    # Damage types are game constants (13 canonical types from SRD page 97)
    parsed_damage_types = parse_damage_types(ruleset)

    # Parse skills (v0.20.0)
    # Skills are game constants (18 skills from SRD pages 76-79)
    parsed_skills = parse_skills(ruleset)

    # Parse weapon_properties (v0.20.0)
    # Weapon properties are game constants (11 properties from SRD page 147)
    parsed_weapon_properties = parse_weapon_properties(ruleset)

    # Build prose datasets (v0.10.0+)
    # Generic config-driven approach for conditions, diseases, madness, poisons
    # (pdf_files already resolved above for lineage extraction)

    # Extract features (v0.11.0)
    # Features come from PDF extraction: class features + lineage traits
    features_doc = None
    if pdf_files and "features" not in skip_datasets:
        try:
            print(f"Extracting features from {pdf_files[0].name}...")
            raw_class_features = extract_class_features(pdf_files[0])
            class_features = parse_features(
                raw_class_features,
                "class",
                ruleset=ruleset,
                class_data=class_data,
            )

            raw_lineage_traits = extract_lineage_traits(pdf_files[0])
            lineage_traits = parse_features(
                raw_lineage_traits,
                "lineage",
                ruleset=ruleset,
                lineage_data=lineage_data,
            )

            all_features = class_features + lineage_traits
            print(
                f"✓ Extracted {len(all_features)} features ({len(class_features)} class + {len(lineage_traits)} lineage)"
            )
        except Exception as exc:
            print(f"⚠️ Feature extraction failed: {exc}")
            all_features = []
    else:
        all_features = []

    # Map dataset names to their parser functions
    # NOTE: Diseases are prose. Madness and poisons use tables + prose descriptions.
    prose_parsers = {
        "conditions": parse_condition_records,
        "diseases": parse_disease_records,
        "poison_descriptions": parse_poison_description_records,
    }

    # Build prose datasets
    conditions_doc = None
    diseases_doc = None
    poison_descriptions_by_name = {}

    # Poisons items come from table + descriptions (table itself goes to tables.json)
    poisons_doc = None

    if pdf_files:
        for dataset_name, parser_func in prose_parsers.items():
            try:
                doc = assemble_prose_dataset(dataset_name, pdf_files[0], parser_func, ruleset)
                # Assign to appropriate variable
                if dataset_name == "conditions":
                    conditions_doc = doc
                elif dataset_name == "diseases":
                    diseases_doc = doc
                elif dataset_name == "poison_descriptions":
                    # Build lookup map for merging with poison table data
                    output_key = TABLES[dataset_name].get("output_key", "items")
                    for desc in doc.get(output_key, []):
                        simple_name = desc.get("simple_name")
                        if simple_name:
                            poison_descriptions_by_name[simple_name] = desc
            except Exception as exc:
                print(f"⚠️ {dataset_name.capitalize()} extraction failed: {exc}")

    # Extract metadata from PDF if present - do this BEFORE building final docs
    pdf_metadata = None
    pdf_files_for_meta = sorted(layout["raw"].glob("*.pdf"))
    if pdf_files_for_meta:
        try:
            pdf_metadata = extract_pdf_metadata(pdf_files_for_meta[0])
            print(f"✓ Extracted metadata from {pdf_files[0].name}")
        except Exception as exc:
            print(f"⚠️ PDF metadata extraction failed: {exc}")

    # Build poison items from table + descriptions (tables themselves go to tables.json)
    if parsed_tables:
        # Build poison items from table + descriptions
        poisons_table = None
        for table in parsed_tables:
            if table.get("simple_name") == "poisons":
                poisons_table = table
                break

        if poisons_table:
            try:
                # Parse poison table into individual item records (equipment-style)
                parsed_poisons = parse_poisons_table(
                    poisons_table, ruleset, descriptions=poison_descriptions_by_name
                )

                # Postprocess: normalize IDs and polish text
                processed_poisons = [clean_poison_record(p) for p in parsed_poisons]

                # Wrap as items array with proper _meta
                poisons_doc = wrap_with_meta(
                    {"items": processed_poisons},
                    ruleset=ruleset,
                    schema_version=read_schema_version("poison"),
                )
                print(f"✓ Parsed {len(processed_poisons)} poison items")
            except Exception as exc:
                print(f"⚠️ Poison item parsing failed: {exc}")

    # Build features document (v0.11.0)
    if all_features:
        # Postprocess: normalize IDs and polish text
        processed_features_list = [clean_feature_record(f) for f in all_features]
        features_doc = wrap_with_meta(
            {"features": processed_features_list},
            ruleset=ruleset,
            schema_version=read_schema_version("features"),
        )

    _write_datasets(
        ruleset=ruleset,
        dist_data_dir=target_dir,
        monsters=parsed_monsters,
        equipment=parsed_equipment if parsed_equipment else None,
        spells=parsed_spells if parsed_spells else None,
        magic_items=parsed_magic_items if parsed_magic_items else None,
        tables=parsed_tables if parsed_tables else None,
        lineages=parsed_lineages if parsed_lineages else None,
        classes=parsed_classes if parsed_classes else None,
        ability_scores=parsed_ability_scores if parsed_ability_scores else None,
        damage_types=parsed_damage_types if parsed_damage_types else None,
        skills=parsed_skills if parsed_skills else None,
        weapon_properties=parsed_weapon_properties if parsed_weapon_properties else None,
        conditions=conditions_doc if conditions_doc else None,
        diseases=diseases_doc if diseases_doc else None,
        poisons=poisons_doc if poisons_doc else None,
        features=features_doc if features_doc else None,
        rules=parsed_rules if parsed_rules else None,
        spell_classes_map=spell_classes_map or None,
    )

    # Read PDF hash from pdf_meta.json (if present)
    pdf_meta_path = layout["raw"] / "pdf_meta.json"
    pdf_hash = None
    if pdf_meta_path.exists():
        pdf_meta = json.loads(pdf_meta_path.read_text(encoding="utf-8"))
        if isinstance(pdf_meta, dict):
            pdf_hash = pdf_meta.get("pdf_sha256")

    # Compute page range from raw monsters for provenance
    monsters_page_range = None
    if raw_monsters:
        all_pages = []
        for monster in raw_monsters:
            pages = monster.get("pages", [])
            if isinstance(pages, list):
                all_pages.extend(pages)
        if all_pages:
            monsters_page_range = (min(all_pages), max(all_pages))

    # Compute page range from equipment (now from parsed_equipment since we assemble from tables)
    equipment_page_range = None
    if parsed_equipment:
        all_pages = [page for item in parsed_equipment if (page := item.get("page"))]
        if all_pages:
            equipment_page_range = (min(all_pages), max(all_pages))

    # Compute page range from raw spells
    spells_page_range = None
    if raw_spells:
        all_pages = [page for spell in raw_spells if (page := spell.get("page"))]
        if all_pages:
            spells_page_range = (min(all_pages), max(all_pages))

    # Generate comprehensive page_index from table_indexer (v0.7.0)
    # Pass list of successfully extracted table IDs for accurate reporting
    extracted_table_ids = [t["id"] for t in parsed_tables] if parsed_tables else None
    table_page_index = _generate_table_page_index(layout["raw"], extracted_table_ids)

    # Generate rich meta.json for consumers (includes license, page_index, etc.)
    meta_json = generate_meta_json(
        ruleset=ruleset,
        pdf_hash=pdf_hash,
        pdf_metadata=pdf_metadata,
        monsters_complete=len(parsed_monsters) > 0,
        monsters_page_range=monsters_page_range,
        equipment_complete=len(parsed_equipment) > 0,
        equipment_page_range=equipment_page_range,
        spells_complete=len(parsed_spells) > 0,
        spells_page_range=spells_page_range,
        table_page_index=table_page_index,
        classes_complete=len(parsed_classes) > 0,
        dist_dir=target_dir,
    )
    meta_path = target_dir / "meta.json"
    meta_path.write_text(_render_json(meta_json), encoding="utf-8")

    # Copy collateral for production bundle
    if bundle:
        _copy_bundle_collateral(target_dir)

    return report_path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out)

    # Parse skip list from various flags
    skip_datasets = set()
    if args.tables_only:
        skip_datasets = {"monsters", "equipment", "spells"}
    elif args.monsters_only:
        skip_datasets = {"equipment", "spells", "tables"}
    elif args.equipment_only:
        skip_datasets = {"monsters", "spells", "tables"}
    elif args.spells_only:
        skip_datasets = {"monsters", "equipment", "tables"}
    elif args.skip:
        skip_datasets = {s.strip() for s in args.skip.split(",")}

    build(
        ruleset=args.ruleset,
        output_format=args.format,
        out_dir=out_dir,
        bundle=args.bundle,
        skip_datasets=skip_datasets,
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entrypoint
    raise SystemExit(main())
