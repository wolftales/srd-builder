#!/usr/bin/env python3
"""Sync count/schema tables in docs + release_check.sh from dist/srd_5_1/meta.json.

ARCHITECTURE.md declares meta.json the authoritative source for item counts and
schema versions. This script makes that mechanical: each managed region is
bracketed by ``AUTO-SYNC:<region> START`` / ``AUTO-SYNC:<region> END`` sentinels,
and the renderer for that region regenerates the content between them from
``meta.json``.

Run without args to rewrite files in place. ``--check`` exits 1 on drift without
writing — wire that into CI / pre-commit.

Curated free-text columns (Description, Notes) live in the dicts at the top of
this file. Edit them here when you want the docs to say something different;
the counts/schemas always come from meta.json.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_META = REPO_ROOT / "dist" / "srd_5_1" / "meta.json"

# ---------------------------------------------------------------------------
# Curated text — edit when you want the human-facing prose to change.
# Keys must match the dataset names in meta.json.datasets.
# ---------------------------------------------------------------------------

DATASET_DISPLAY_NAME: dict[str, str] = {
    "ability_scores": "Ability Scores",
    "classes": "Classes",
    "conditions": "Conditions",
    "damage_types": "Damage Types",
    "diseases": "Diseases",
    "equipment": "Equipment",
    "features": "Features",
    "lineages": "Lineages",
    "magic_items": "Magic Items",
    "monsters": "Monsters",
    "poisons": "Poisons",
    "rules": "Rules",
    "skills": "Skills",
    "spells": "Spells",
    "tables": "Tables",
    "weapon_properties": "Weapon Properties",
}

DATASET_DESCRIPTION: dict[str, str] = {
    "ability_scores": "Atomic reference: STR/DEX/CON/INT/WIS/CHA",
    "classes": "Character classes with progression",
    "conditions": "Status conditions (poisoned, stunned, etc.)",
    "damage_types": "Atomic reference: damage type vocabulary",
    "diseases": "Cackle Fever, Sewer Plague, Sight Rot",
    "equipment": "Weapons, armor, adventuring gear",
    "features": "Class features and lineage traits",
    "lineages": "Races/lineages with traits",
    "magic_items": "Magic items with descriptions",
    "monsters": "Monsters, creatures, and NPCs",
    "poisons": "Poison gear entries + descriptions",
    "rules": "Core mechanics from 7 chapters",
    "skills": "Atomic reference: skill vocabulary",
    "spells": "Spell list with effects, components, casting",
    "tables": "Reference tables (equipment, expenses, services, madness)",
    "weapon_properties": "Atomic reference: weapon property vocabulary",
}

DATASET_NOTE: dict[str, str] = {
    "monsters": "Pages 261\u2013394; 27 fields, 100% required coverage",
    "spells": "Cantrip through 9th, all 8 schools",
    "equipment": "Weapons, armor, adventuring gear (11 weapon properties)",
    "features": "Class features and lineage traits",
    "magic_items": "Magic items with descriptions",
    "rules": "7 chapters of core mechanics",
    "tables": "Equipment, expenses, services, madness, etc.",
    "skills": "Atomic reference",
    "conditions": "Status conditions",
    "poisons": "Poison gear + descriptions",
    "damage_types": "Atomic reference",
    "lineages": "9 base + 4 subraces",
    "classes": "Full progression tables (levels 1\u201320)",
    "weapon_properties": "Atomic reference",
    "ability_scores": "STR/DEX/CON/INT/WIS/CHA",
    "diseases": "Cackle Fever, Sewer Plague, Sight Rot",
}

SCHEMA_FOR_DATASET: dict[str, str] = {
    "ability_scores": "ability_score",
    "classes": "class",
    "conditions": "condition",
    "damage_types": "damage_type",
    "diseases": "disease",
    "equipment": "equipment",
    "features": "features",
    "lineages": "lineage",
    "magic_items": "magic_item",
    "monsters": "monster",
    "poisons": "poison",
    "rules": "rule",
    "skills": "skill",
    "spells": "spell",
    "tables": "table",
    "weapon_properties": "weapon_property",
}

# ---------------------------------------------------------------------------
# Meta loading
# ---------------------------------------------------------------------------


def load_meta(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"error: {path} not found. Run `make bundle` first so meta.json exists.")
    return json.loads(path.read_text())


def schema_for(meta: dict, dataset: str) -> str:
    return meta["schemas"][SCHEMA_FOR_DATASET[dataset]]


def total_items(meta: dict) -> int:
    return sum(entry["count"] for entry in meta["datasets"].values())


def dataset_count(meta: dict, dataset: str) -> int:
    return meta["datasets"][dataset]["count"]


def all_datasets(meta: dict) -> list[str]:
    return sorted(meta["datasets"].keys())


def datasets_by_count_desc(meta: dict) -> list[str]:
    return sorted(
        meta["datasets"].keys(),
        key=lambda d: (-meta["datasets"][d]["count"], d),
    )


# ---------------------------------------------------------------------------
# Renderers — each returns the content (without sentinel lines).
# Markdown renderers return content suitable for embedding between
# ``<!-- AUTO-SYNC:... START -->`` and ``<!-- AUTO-SYNC:... END -->``.
# Shell renderers return content suitable for embedding between
# ``# AUTO-SYNC:... START`` and ``# AUTO-SYNC:... END``.
# ---------------------------------------------------------------------------


def render_readme_totals(meta: dict) -> str:
    return (
        f"Latest build: **{total_items(meta):,} items across "
        f"{len(meta['datasets'])} datasets** (counts and schema versions "
        f"are written to\n"
        f"`dist/srd_5_1/meta.json` on every build)."
    )


def render_readme_dataset_table(meta: dict) -> str:
    lines = [
        "| Dataset | Count | Schema |",
        "|---|---:|---|",
    ]
    for dataset in datasets_by_count_desc(meta):
        lines.append(
            f"| {DATASET_DISPLAY_NAME[dataset]} | "
            f"{dataset_count(meta, dataset)} | "
            f"{schema_for(meta, dataset)} |"
        )
    return "\n".join(lines)


def render_readme_bundle_tree(meta: dict) -> str:
    name_width = max(len(f"{d}.json") for d in meta["datasets"]) + 1
    body_lines = [
        f"├── {f'{d}.json':<{name_width}} # {dataset_count(meta, d)}" for d in all_datasets(meta)
    ]
    return "\n".join(
        [
            "```",
            "dist/srd_5_1/",
            *body_lines,
            "├── index.json             # Cross-dataset lookup with aliases",
            "├── meta.json              # Versions, license, inventory, schema map",
            "├── build_report.json      # Build provenance (timestamp, builder version, sources)",
            "├── quality_report.json    # Audit findings from scripts/quality_report.py",
            "├── README.md              # Auto-generated consumer-facing README",
            "├── schemas/               # 16 schemas + schemas/exemplars/ (one valid instance each)",
            "└── docs/                  # SCHEMAS.md, DATA_DICTIONARY.md",
            "```",
        ]
    )


def render_architecture_version(meta: dict) -> str:
    return f"**Version:** v{meta['builder_version']}"


def render_architecture_total_line(meta: dict) -> str:
    return (
        f"SRD-Builder extracts structured JSON datasets from the SRD 5.1 PDF. "
        f"The v{meta['builder_version']} build ships "
        f"**{len(meta['datasets'])} datasets** containing "
        f"**{total_items(meta):,} items**:"
    )


def render_architecture_overview_table(meta: dict) -> str:
    lines = [
        "| File | Count | Schema | Description |",
        "|------|------:|--------|-------------|",
    ]
    for dataset in all_datasets(meta):
        filename = f"`{dataset}.json`"
        lines.append(
            f"| {filename} | "
            f"{dataset_count(meta, dataset)} | "
            f"v{schema_for(meta, dataset)} | "
            f"{DATASET_DESCRIPTION[dataset]} |"
        )
    return "\n".join(lines)


def render_architecture_stats_table(meta: dict) -> str:
    lines = [
        "| Dataset | Count | Notes |",
        "|---------|------:|-------|",
    ]
    for dataset in datasets_by_count_desc(meta):
        lines.append(f"| {dataset} | {dataset_count(meta, dataset)} | {DATASET_NOTE[dataset]} |")
    lines.append(f"| **Total** | **{total_items(meta):,}** | |")
    return "\n".join(lines)


def render_architecture_stats_header(meta: dict) -> str:
    return f"### Dataset Statistics (v{meta['builder_version']})"


def render_integration_bundle_header(meta: dict) -> str:
    return f"## Bundle Layout (v{meta['builder_version']})"


def render_integration_bundle_tree(meta: dict) -> str:
    name_width = max(len(f"{d}.json") for d in meta["datasets"]) + 5
    body_lines = [
        f"├── {f'{d}.json':<{name_width}}# "
        f"{dataset_count(meta, d):<5} (schema v{schema_for(meta, d)})"
        for d in all_datasets(meta)
    ]
    return "\n".join(
        [
            "```",
            "dist/srd_5_1/",
            "├── README.md                  # Generated dynamically from meta.json",
            "├── meta.json                  # Source of truth for inventory + schema manifest",
            "├── index.json                 # Cross-dataset lookup maps",
            "├── build_report.json          # Per-stage parse/postprocess counts",
            "│",
            *body_lines,
            "│",
            "├── schemas/                   # All 16 JSON Schema files (copies of /schemas/)",
            "└── docs/                      # DATA_DICTIONARY.md, SCHEMAS.md (shipped to consumers)",
            "```",
        ]
    )


def render_integration_totals(meta: dict) -> str:
    return f"**Totals shipped:** {len(meta['datasets'])} datasets, {total_items(meta):,} items."


def render_release_check_expected(meta: dict) -> str:
    lines = ["declare -A EXPECTED=("]
    for dataset in all_datasets(meta):
        lines.append(f'  ["{dataset}.json"]={dataset_count(meta, dataset)}')
    lines.append(")")
    lines.append("")
    lines.append("# All datasets use the 'items' key since v0.30.0.")
    lines.append("declare -A KEYS=()")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sentinel-driven replacement
# ---------------------------------------------------------------------------

# Each managed region: (file relative to repo root, sentinel name, renderer)
# Sentinel syntax is inferred from file extension: .md -> HTML comments,
# .sh / .py -> shell-style ``# ...`` comments.

Region = tuple[str, str, Callable[[dict], str]]

REGIONS: list[Region] = [
    ("README.md", "readme:totals-prefix", render_readme_totals),
    ("README.md", "readme:dataset-table", render_readme_dataset_table),
    ("README.md", "readme:bundle-tree", render_readme_bundle_tree),
    ("docs/ARCHITECTURE.md", "arch:version", render_architecture_version),
    ("docs/ARCHITECTURE.md", "arch:total-line", render_architecture_total_line),
    ("docs/ARCHITECTURE.md", "arch:overview-table", render_architecture_overview_table),
    ("docs/ARCHITECTURE.md", "arch:stats-header", render_architecture_stats_header),
    ("docs/ARCHITECTURE.md", "arch:stats-table", render_architecture_stats_table),
    ("docs/INTEGRATION.md", "int:bundle-header", render_integration_bundle_header),
    ("docs/INTEGRATION.md", "int:bundle-tree", render_integration_bundle_tree),
    ("docs/INTEGRATION.md", "int:totals", render_integration_totals),
    ("scripts/release_check.sh", "check:expected", render_release_check_expected),
]


def _sentinel_pair(file_path: Path, region: str) -> tuple[str, str]:
    suffix = file_path.suffix
    if suffix == ".md":
        return (
            f"<!-- AUTO-SYNC:{region} START -->",
            f"<!-- AUTO-SYNC:{region} END -->",
        )
    if suffix in (".sh", ".py", ".bash", ".zsh", ".yaml", ".yml", ".toml"):
        return (f"# AUTO-SYNC:{region} START", f"# AUTO-SYNC:{region} END")
    raise ValueError(f"unknown comment style for {file_path}")


def _replace_region(text: str, start: str, end: str, new_content: str) -> str:
    pattern = re.compile(
        r"^(?P<indent>[ \t]*)" + re.escape(start) + r"\n.*?\n[ \t]*" + re.escape(end),
        re.DOTALL | re.MULTILINE,
    )

    def _repl(match: re.Match[str]) -> str:
        indent = match.group("indent")
        if indent:
            body = "\n".join((indent + line) if line else "" for line in new_content.split("\n"))
        else:
            body = new_content
        return f"{indent}{start}\n{body}\n{indent}{end}"

    return pattern.sub(_repl, text, count=1)


def _find_region(text: str, start: str, end: str) -> bool:
    return start in text and end in text


def sync_file(path: Path, regions: list[Region], meta: dict) -> tuple[bool, list[str]]:
    """Apply every region for ``path``. Return ``(changed, problems)``."""
    original = path.read_text()
    updated = original
    problems: list[str] = []
    for _, region_name, renderer in regions:
        start, end = _sentinel_pair(path, region_name)
        if not _find_region(updated, start, end):
            problems.append(f"{path}: sentinels for '{region_name}' not found")
            continue
        new_content = renderer(meta)
        updated = _replace_region(updated, start, end, new_content)
    if updated != original:
        path.write_text(updated)
        return True, problems
    return False, problems


def check_file(path: Path, regions: list[Region], meta: dict) -> tuple[bool, list[str]]:
    """Return ``(drift, problems)`` without writing."""
    original = path.read_text()
    updated = original
    problems: list[str] = []
    for _, region_name, renderer in regions:
        start, end = _sentinel_pair(path, region_name)
        if not _find_region(updated, start, end):
            problems.append(f"{path}: sentinels for '{region_name}' not found")
            continue
        updated = _replace_region(updated, start, end, renderer(meta))
    return updated != original, problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync count/schema tables from meta.json.")
    parser.add_argument(
        "--meta",
        type=Path,
        default=DEFAULT_META,
        help=f"Path to meta.json (default: {DEFAULT_META.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 if any managed region is out of sync; do not write.",
    )
    args = parser.parse_args()

    meta = load_meta(args.meta)

    # Group regions by file so we open each file once.
    by_file: dict[str, list[Region]] = {}
    for region in REGIONS:
        by_file.setdefault(region[0], []).append(region)

    any_drift = False
    any_problem = False
    for rel_path, regions in by_file.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            print(f"skip: {rel_path} not found", file=sys.stderr)
            any_problem = True
            continue
        if args.check:
            drift, problems = check_file(path, regions, meta)
            for p in problems:
                print(p, file=sys.stderr)
                any_problem = True
            if drift:
                print(f"drift: {rel_path}", file=sys.stderr)
                any_drift = True
        else:
            changed, problems = sync_file(path, regions, meta)
            for p in problems:
                print(p, file=sys.stderr)
                any_problem = True
            if changed:
                print(f"rewrote: {rel_path}")

    if args.check and (any_drift or any_problem):
        print(
            "\nDocs are out of sync with meta.json. "
            "Run `python scripts/sync_doc_tables.py` to fix.",
            file=sys.stderr,
        )
        sys.exit(1)
    if any_problem:
        sys.exit(1)


if __name__ == "__main__":
    main()
